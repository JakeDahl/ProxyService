import os

import requests
import json
import random

def get_random_us_ip():
	# 'https://cdn-lite.ip2location.com/datasets/US.json'
	f = open(os.getcwd() + '/proxy_service/configs/us-ip-range.json', 'r')
	j = json.loads(f.read())

	rand_idx = random.randrange(0, len(j['data']))

	range1 = j['data'][rand_idx][0].split('.')
	range2 = j['data'][rand_idx][1].split('.')

	random_ip = []
	for idx in range(0, 4):
		if int(range1[idx]) - int(range2[idx]) == 0:
			random_ip.append(str(range1[idx]))
			continue
		rand_ip_val = random.randrange(int(range1[idx]), int(range2[idx]))
		random_ip.append(str(rand_ip_val))

	ip_address = '.'.join(random_ip)
	return ip_address
