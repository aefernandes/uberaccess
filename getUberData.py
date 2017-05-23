import ConfigParser
import json
import time
import grequests
import sys
import os
import csv
import urllib
import logging
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# API end points
price_url = "https://api.uber.com/v1/estimates/price"
time_url = "https://api.uber.com/v1/estimates/time"

# parse configuration information to get uber server tokens
config = ConfigParser.ConfigParser()
config.read(os.path.dirname(os.path.abspath(__file__)) + "/configA.conf")
uber_server_tokens = (config.get("MainConfig", "uber_server_tokens")).split(",")

# parse locations and output file name
locations = json.loads(config.get("MainConfig", "locations"))
d = json.loads(config.get("MainConfig","destination"))
output_file_name = config.get("MainConfig", "output_file_name")
time = int(config.get("MainConfig", "time"))

# create file to store data
fileWriter = csv.writer(open(output_file_name, "w+"),delimiter=",")
fileWriter.writerow(["timestamp", "object_id", "start_location_id", "end_location_id", "product_type", "expected_wait_time", "low_estimate", "high_estimate", "surge_multiplier", "distance", "duration"])
	
# create api_param objects to send requests to API, one for each start and end location to gather
api_params = []
for l in locations:
	start_location_id = l["location_id"]
	end_location_id = d["location_id"]
	price_parameters = {
		'start_latitude': l["latitude"],
		'start_longitude': l["longitude"],
		'end_latitude': d["latitude"],
		'end_longitude': d["longitude"]
	}

	time_parameters = {
		'start_latitude': l["latitude"],
		'start_longitude': l["longitude"]
	}
	object_id = l["OBJECTID"]

# make separate requests for price and time
	api_params.append({"url": price_url, "start_location_id": start_location_id, "end_location_id": end_location_id, "type": "price", "parameters": price_parameters, "object_id": object_id})
	api_params.append({"url": time_url, "start_location_id": start_location_id, "end_location_id": end_location_id, "type": "time", "parameters": time_parameters, "object_id": object_id})

# switch to local time zone
local_tz = pytz.timezone('US/Eastern')

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)

def aslocaltimestr(utc_dt):
    return utc_to_local(utc_dt).strftime('%Y-%m-%d %H:%M:%S')


tokennum = 0
def gather_loop():
	global tokennum
	# make list to hold our things to do via async
	async_action_items = []

	# use one dictionary for every pair of requests
	common_data_dicts = []
	for i in range (0,len(api_params) / 2):
		common_data_dicts.append({})

	for i, api_param in enumerate(api_params):
		# get current time
		api_param["datetime"] = aslocaltimestr(datetime.utcnow())
		api_param["data"] = common_data_dicts[(int)(i / 2)]
		api_param["parameters"]["server_token"] = uber_server_tokens[tokennum % len(uber_server_tokens)]		
		# found at http://stackoverflow.com/questions/25115151/how-to-pass-parameters-to-hooks-in-python-grequests
		action_item = grequests.get(api_param["url"]+"?"+urllib.urlencode(api_param["parameters"]), hooks={'response': [hook_factory(api_param)]})
		async_action_items.append(action_item)
		# increment token num to use next server key next time
		tokennum = tokennum + 1

	# initiate both requests in parallel
	grequests.map(async_action_items)


def hook_factory(*factory_args, **factory_kwargs):
	def it_responded(res, **kwargs):
		call_type = factory_args[0]["type"]
		start_location_id = factory_args[0]["start_location_id"]
		end_location_id = factory_args[0]["end_location_id"]
		current_time = factory_args[0]["datetime"]
		data_dict = factory_args[0]["data"]
		object_id = factory_args[0]["object_id"]
		try:
			json_response = json.loads(res.content)
			# parse data differently depending on the type of call it was
			try:
				if call_type == "time":
					for t in json_response["times"]:
						if t["display_name"] not in data_dict:
							data_dict[t["display_name"]] = {}
						data_dict[t["display_name"]]["expected_wait_time"] = t["estimate"]
				elif call_type == "price":
					for p in json_response["prices"]:
						if p["display_name"] not in data_dict:
							data_dict[p["display_name"]] = {}

						data_dict[p["display_name"]]["surge_multiplier"] = p["surge_multiplier"]
						data_dict[p["display_name"]]["product_type"] = p["display_name"]
						data_dict[p["display_name"]]["low_estimate"] = p["low_estimate"]
						if data_dict[p["display_name"]]["low_estimate"] != None:
							data_dict[p["display_name"]]["low_estimate"] = int(data_dict[p["display_name"]]["low_estimate"])

						data_dict[p["display_name"]]["high_estimate"] = p["high_estimate"]
						if data_dict[p["display_name"]]["high_estimate"] != None:
							data_dict[p["display_name"]]["high_estimate"] = int(data_dict[p["display_name"]]["high_estimate"])

						data_dict[p["display_name"]]["distance"] = p["distance"]
						data_dict[p["display_name"]]["duration"] = p["duration"]

				# write row for each product in data dict
				for p in data_dict:
					data_dict[p]["timestamp"] = current_time
					data_dict[p]["start_location_id"] = start_location_id
					data_dict[p]["end_location_id"] = end_location_id
					data_dict[p]["object_id"] = object_id
					# store if contains time and price
					if "expected_wait_time" in data_dict[p] and "high_estimate" in data_dict[p]:
						fileWriter.writerow([data_dict[p]["timestamp"], data_dict[p]["object_id"], data_dict[p]["start_location_id"], data_dict[p]["end_location_id"], data_dict[p]["product_type"], data_dict[p]["expected_wait_time"], data_dict[p]["low_estimate"], data_dict[p]["high_estimate"], data_dict[p]["surge_multiplier"], data_dict[p]["distance"], data_dict[p]["duration"]])
			except TypeError as e:
				print(e)

		except Exception as e:
			print "The response at " + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + " was: "
			print json_response
			print res.content
			print e

	return it_responded


# create scheduler to trigger every N seconds
# http://apscheduler.readthedocs.org/en/3.0/userguide.html#code-examples
logging.basicConfig()
scheduler = BackgroundScheduler()
scheduler.add_job(gather_loop, 'interval', seconds = time)
scheduler.start()

while True:
	time.sleep(1)

# run from command line: nohup python -u getUberData3.py > nohup.txt &
# modified from https://github.com/comp-journalism/uberpy
