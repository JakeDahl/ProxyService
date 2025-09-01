import boto3
import json
from rotator import Proxy


def lambda_handler(event, context):
	print(event)
	proxy = Proxy()

	resources_to_rotate = {}

	for record in event['Records']:
		j = json.loads(record['body'])
		print(j)
	# 	pr = j['proxy_resource']
	# 	resources_to_rotate[pr] = pr
	#
	# for resource in resources_to_rotate:
	# 	proxy.rotate_proxy(resource)
	#
	# proxy.deploy_proxies()
