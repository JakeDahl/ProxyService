import boto3
import json
from rotator import Proxy


def lambda_handler(event, context):
	proxy = Proxy()

	for proxy_name in proxy.api_config['proxies']:
		proxy.rotate_proxy(proxy_name)

	proxy.deploy_proxies()
