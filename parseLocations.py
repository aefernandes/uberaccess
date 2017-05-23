import json

# open geojson file from QGIS
with open('pointpoly.geojson') as data_file:    
    data = json.load(data_file)

# convert to format parseable by Uber API
locations = []
count = 1
for item in data["features"]:
	point = dict()
	point["id"] = item["properties"]["id"]
	if point["id"] == 0:	# select one point from each neighborhood in QGIS map
		print(item)
		point["OBJECTID"] = item["properties"]["OBJECTID"]
		point["latitude"] = item["geometry"]["coordinates"][1]
		point["longitude"] = item["geometry"]["coordinates"][0]
		point["location_id"] = count
		locations.append(point)
		count += 1
		print(point)

result = json.dumps(locations)

# write as array of locations to config file 
with open("config.conf", "a+") as myfile:
	if "locations" not in myfile.read():
		myfile.write("\n"+"locations = "+str(result))