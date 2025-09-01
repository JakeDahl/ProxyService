import os
#
# from rotator import Proxy
#
os.environ['config_bucket'] = 'proxyservicestack-proxyconstructconfigbucketd8424d-8um3nh9w1kea'
os.environ['rest_api_id'] = 'zwzdw9k4bg'


import json
from proxy_service.forward_proxy.handler import lambda_handler

test_event = {'Records': [{'messageId': 'd45d7edf-8be2-434b-bd7d-e61354f529ab','body': '{"version":"0","id":"e7ba45ae-3af0-ef96-812c-a63dcb56129a","detail-type":"AWS API Call via CloudTrail","source":"aws.logs","account":"229133519362","time":"2025-09-01T12:23:16Z","region":"us-east-1","resources":[],"detail":{"eventVersion":"1.11","userIdentity":{"type":"AssumedRole","principalId":"AROATKWLMBIBEBFU3R7GD:BackplaneAssumeRoleSession","arn":"arn:aws:sts::229133519362:assumed-role/ProxyServiceStack-proxyconstructproxyapimainCloudWa-h22lBmEltidr/BackplaneAssumeRoleSession","accountId":"229133519362","sessionContext":{"sessionIssuer":{"type":"Role","principalId":"AROATKWLMBIBEBFU3R7GD","arn":"arn:aws:iam::229133519362:role/ProxyServiceStack-proxyconstructproxyapimainCloudWa-h22lBmEltidr","accountId":"229133519362","userName":"ProxyServiceStack-proxyconstructproxyapimainCloudWa-h22lBmEltidr"},"attributes":{"creationDate":"2025-09-01T12:23:16Z","mfaAuthenticated":"false"}},"invokedBy":"apigateway.amazonaws.com"},"eventTime":"2025-09-01T12:23:16Z","eventSource":"logs.amazonaws.com","eventName":"CreateLogStream","awsRegion":"us-east-1","sourceIPAddress":"apigateway.amazonaws.com","userAgent":"apigateway.amazonaws.com","requestParameters":{"logGroupName":"ProxyServiceStack-proxyconstructapilogsD57705A6-Xi8fHFlglEOP","logStreamName":"a5d5ed10233f0f0501701489d21438d5"},"responseElements":null,"requestID":"2aebcc3a-59a3-4842-8257-ef3a201801db","eventID":"ad02339a-7e1f-4e58-82c6-509796d2e2be","readOnly":false,"eventType":"AwsApiCall","apiVersion":"20140328","managementEvent":true,"recipientAccountId":"229133519362","eventCategory":"Management"}}', 'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1756729407952', 'SenderId': 'AIDAJXNJGGKNS7OSV23OI', 'ApproximateFirstReceiveTimestamp': '1756729408015'}, 'messageAttributes': {}, 'md5OfMessageAttributes': None, 'md5OfBody': 'bc7089a273416976f33e8f9f37926c48', 'eventSource': 'aws:sqs', 'eventSourceARN': 'arn:aws:sqs:us-east-1:229133519362:ProxyServiceStack-proxyconstructiprotationqueue462335B0-wEtxWamnShoE', 'awsRegion': 'us-east-1'}]}


test_records = {'Records': [{'body': json.dumps(test_event)}]}
lambda_handler(test_records, None)
