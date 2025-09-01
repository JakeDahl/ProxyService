import os
import boto3
import uuid
import ipaddress
import json
from random import randint
from ip_range_puller import get_random_us_ip


class Proxy:
	def __init__(self):
		config_bucket = os.environ['config_bucket']
		self.rest_api_id = os.environ['rest_api_id']

		self.uid = uuid.uuid4().hex
		self.apig = boto3.client('apigateway')
		s3_client = boto3.client('s3')

		config_json = s3_client.get_object(
			Bucket=config_bucket,
			Key='configs/config.json'
		)

		self.api_config = json.loads(config_json['Body'].read())
		self.sqs_client = boto3.client('sqs')

	@staticmethod
	def _get_random_ip_address():
		MAX_IPV4 = ipaddress.IPv4Address._ALL_ONES
		rand_ip = ipaddress.IPv4Address._string_from_ip_int(randint(0, MAX_IPV4))
		return rand_ip

	def rotate_proxy(self, proxy_name):
		get_resource_response = self.apig.get_resources(
			restApiId=self.rest_api_id
		)

		rand_ip = get_random_us_ip()
		proxy_item = None
		for item in get_resource_response['items']:
			if 'pathPart' in item and item['pathPart'] == 'proxy':
				proxy_item = item

		proxy_endpoint = [
			x for x in get_resource_response['items']
			if 'parentId' in x
			   and x['parentId'] == proxy_item['id']
			   and x['pathPart'] == proxy_name
		][0]

		proxy_sub_endpoint = [
			x for x in get_resource_response['items']
			if 'parentId' in x
			   and x['parentId'] == proxy_endpoint['id']
			   and x['pathPart'] == '{proxy+}'
		][0]

		proxy_md = self.api_config['proxies'][proxy_name]

		self.apig.put_integration(
			restApiId=self.rest_api_id,
			resourceId=proxy_endpoint["id"],
			type="HTTP_PROXY",
			httpMethod="ANY",
			integrationHttpMethod="ANY",
			uri=proxy_md['url'],
			connectionType="INTERNET",
			requestParameters={
				"integration.request.path.proxy": "method.request.path.proxy",
				"integration.request.header.X-Forwarded-For": "'{}'".format(rand_ip)
			}
		)
		self.apig.put_integration(
			restApiId=self.rest_api_id,
			resourceId=proxy_sub_endpoint["id"],
			type="HTTP_PROXY",
			httpMethod="ANY",
			integrationHttpMethod="ANY",
			uri=proxy_md['url'] + "/{proxy}",
			connectionType="INTERNET",
			requestParameters={
				"integration.request.path.proxy": "method.request.path.proxy",
				"integration.request.header.X-Forwarded-For": "'{}'".format(rand_ip)
			}
		)

	def deploy_proxies(self):
		deployment = self.apig.create_deployment(
			restApiId=self.rest_api_id,
			stageName='prod'
		)
		return deployment
