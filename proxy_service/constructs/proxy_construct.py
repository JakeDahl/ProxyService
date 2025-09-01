import os
import json

import aws_cdk
from aws_cdk import (
	aws_sqs as sqs,
	aws_cognito as cognito,
	aws_apigateway as apigateway,
	aws_lambda as _lambda,
	BundlingOptions,
	aws_events as events,
	aws_events_targets as targets,
	aws_s3_deployment as s3dep,
	aws_logs as logs
)

from constructs import Construct
from aws_cdk import RemovalPolicy
import ipaddress
from random import randint
from ..constructs.ip_range_puller import get_random_us_ip


def get_random_ip_address():
	MAX_IPV4 = ipaddress.IPv4Address._ALL_ONES
	rand_ip = ipaddress.IPv4Address._string_from_ip_int(randint(0, MAX_IPV4))
	return rand_ip


class ProxyConstruct(Construct):

	def __init__(self, scope: Construct, construct_id: str, id_suffix: str) -> None:
		super().__init__(scope, construct_id)

		ip_rotator_role = aws_cdk.aws_iam.Role(
			self,
			'ip-rotator-role-{}'.format(id_suffix),
			assumed_by=aws_cdk.aws_iam.CompositePrincipal(
				aws_cdk.aws_iam.ServicePrincipal('lambda.amazonaws.com'),
			),
			managed_policies=[
				aws_cdk.aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
			]
		)

		self.config_bucket = aws_cdk.aws_s3.Bucket(
			self,
			'config-bucket',
			# bucket_name='freebie-gen-config-{}'.format(id_suffix),
			removal_policy=RemovalPolicy.DESTROY,
			auto_delete_objects=True
		)

		dep = s3dep.BucketDeployment(
			self,
			id='config_deployment',
			retain_on_delete=False,
			destination_bucket=self.config_bucket,
			sources=[s3dep.Source.asset('proxy_service/configs')],
			destination_key_prefix='configs'
		)

		log_group = logs.LogGroup(
			self,
			'api-logs',
			retention=logs.RetentionDays.ONE_DAY
		)

		self.rest_api = apigateway.RestApi(
			self,
			'proxy-api-{}'.format(id_suffix),
			rest_api_name='proxy-api-{}'.format(id_suffix),
			cloud_watch_role=True,
			deploy_options={
				"access_log_destination": apigateway.LogGroupLogDestination(log_group),
				"access_log_format": apigateway.AccessLogFormat.custom(
					json.dumps({
						"requestId": "$context.requestId",
						"ip": "$context.identity.sourceIp",
						"caller": "$context.identity.caller",
						"user": "$context.identity.user",
						"requestTime": "$context.requestTime",
						"httpMethod": "$context.httpMethod",
						"resourcePath": "$context.resourcePath",
						"status": "$context.status",
						"protocol": "$context.protocol",
						"responseLength": "$context.responseLength"
					})
				)
			}
		)

		self.rest_api.node.add_dependency(dep)

		proxy_resource = self.rest_api.root.add_resource('proxy')

		f = open(os.getcwd() + '/proxy_service/configs/config.json', 'r')
		j = json.load(f)

		# Create IAM role for authorized users
		authorized_arns = j.get('authorized_arns', [])
		
		proxy_access_role = aws_cdk.aws_iam.Role(
			self,
			'proxy-access-role-{}'.format(id_suffix),
			assumed_by=aws_cdk.aws_iam.CompositePrincipal(
				*[aws_cdk.aws_iam.ArnPrincipal(arn) for arn in authorized_arns]
			),
			inline_policies={
				'ProxyAccessPolicy': aws_cdk.aws_iam.PolicyDocument(
					statements=[
						aws_cdk.aws_iam.PolicyStatement(
							effect=aws_cdk.aws_iam.Effect.ALLOW,
							actions=['execute-api:Invoke'],
							resources=[self.rest_api.arn_for_execute_api('*', '/proxy/*')]
						)
					]
				)
			}
		)

		# Generate proxy targets.
		for proxy in j['proxies']:
			random_ip = get_random_us_ip()
			proxy_subresource = proxy_resource.add_resource(proxy)
			proxy_wc_resource = proxy_subresource.add_resource('{proxy+}')

			integration = apigateway.HttpIntegration(
				url=j['proxies'][proxy]['url'],
				http_method="ANY",
				options=apigateway.IntegrationOptions(
					request_parameters={
						"integration.request.path.proxy": "method.request.path.proxy",
						"integration.request.header.X-Forwarded-For": "'{}'".format(random_ip)
					},
					connection_type=apigateway.ConnectionType.INTERNET
				)
			)

			proxy_subresource.add_method(
				http_method='ANY',
				authorization_type=apigateway.AuthorizationType.IAM,
				request_parameters={
					"method.request.path.proxy": True,
					"method.request.header.X-My-X-Forwarded-For": True
				},
				integration=integration
			)

			next_integration = apigateway.HttpIntegration(
				url=j['proxies'][proxy]['url'] + '/{proxy}',
				http_method="ANY",
				options=apigateway.IntegrationOptions(
					request_parameters={
						"integration.request.path.proxy": "method.request.path.proxy",
						"integration.request.header.X-Forwarded-For": "'{}'".format(random_ip)
					},
					connection_type=apigateway.ConnectionType.INTERNET
				)
			)

			proxy_wc_resource.add_method(
				http_method='ANY',
				authorization_type=apigateway.AuthorizationType.IAM,
				request_parameters={
					"method.request.path.proxy": True,
					"method.request.header.X-My-X-Forwarded-For": True
				},
				integration=next_integration
			)

		ip_rotation_dlq = sqs.Queue(
			self,
			'ip-rotation-dlq'
		)

		self.ip_rotation_queue = sqs.Queue(
			self,
			'ip-rotation-queue',
			visibility_timeout=aws_cdk.Duration.seconds(61),
			dead_letter_queue=aws_cdk.aws_sqs.DeadLetterQueue(
				queue=ip_rotation_dlq,
				max_receive_count=2
			)
		)

		ip_rotator_func = _lambda.Function(
			self,
			"ip-rotator-{}".format(id_suffix),
			runtime=_lambda.Runtime.PYTHON_3_11,
			handler="handler.lambda_handler",
			role=ip_rotator_role,
			timeout=aws_cdk.Duration.seconds(60),
			reserved_concurrent_executions=1,
			memory_size=128,
			architecture=_lambda.Architecture.ARM_64,
			code=_lambda.Code.from_asset(
				path="proxy_service/forward_proxy",
				bundling=BundlingOptions(
					image=_lambda.Runtime.PYTHON_3_11.bundling_image,
					command=[
						"bash", "-c",
						"pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
					],
				),
			),
			environment={
				'config_bucket': self.config_bucket.bucket_name,
				'rest_api_id': self.rest_api.rest_api_id,
				'proxy_queue': self.ip_rotation_queue.queue_url,
				'alarm_topic_arn': self.ip_rotation_queue.queue_url
			}
		)

		events.Rule(
			self,
			'event-rule',
			event_pattern={
				"source": ["aws.logs"],
				"detail": {
					"requestParameters": {
						"logGroupName": [log_group.log_group_name]
					}
				}
			},
			targets=[aws_cdk.aws_events_targets.SqsQueue(self.ip_rotation_queue)]
		)

		# Grant permissions for CloudWatch Logs to send messages to the SQS queue
		self.ip_rotation_queue.grant_send_messages(aws_cdk.aws_iam.ServicePrincipal('logs.amazonaws.com'))

		event_source = aws_cdk.aws_lambda_event_sources.SqsEventSource(
			self.ip_rotation_queue,
			batch_size=10000,
			max_batching_window=aws_cdk.Duration.seconds(15)
		)

		ip_rotator_func.add_event_source(event_source)

		ip_rotator_role.add_to_policy(
			aws_cdk.aws_iam.PolicyStatement(
				effect=aws_cdk.aws_iam.Effect.ALLOW,
				resources=[
					self.config_bucket.bucket_arn,
					self.config_bucket.bucket_arn + '/*',
				],
				actions=[
					's3:List*',
					's3:Get*',
				]
			)
		)

		ip_rotator_role.add_to_policy(
			aws_cdk.aws_iam.PolicyStatement(
				effect=aws_cdk.aws_iam.Effect.ALLOW,
				resources=[
					'*'
				],
				actions=[
					'apigateway:*',
				]
			)
		)
