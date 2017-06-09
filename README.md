# Uber's Wheelchair Accessibility

This repository contains the code used to scraping the Uber API for a two-week period and the subsequent data analysis exploring the wheelchair accessibility of Uber rides in NYC. 

## Files Contained

1. getUberData.py
--------------

This script was used to collect data from the Uber API.

Dependencies: 
- https://apscheduler.readthedocs.org/en/latest/
- https://github.com/kennethreitz/grequests

2. config.conf
--------------

This file is used in conjuction with getUberData.py.

Setup:
- Add comma-separated Uber API keys in config.conf
- The list of locations to collect data is inputted as json objects of the form `{"location_id": <int>, "latitude": <float>, "longitude": <float>}`
- The output data file is called results.csv
- The time is currently set to 3600 seconds, or a request to the API every hour
- Important note for rate limiting: the requests for time and price count as two separate API calls

This script runs indefinitely by using a command like: `nohup python -u getUberData.py > nohup.txt &`

3. parseLocations.py
--------------

This script takes the geojson output of a QGIS file and automatically updates the config.conf file used to scrape the Uber API.

Setup:
- Change the input and output files to desired locations

4. pointpoly.geojson
--------------

This is used for the QGIS project.

5. centroidsNYC.qgs
--------------

This is a QGIS project containing the shapefiles for the 195 NTA neighborhoods in NYC. 

Setup:
- Run realcentroid plugin to find centers of each neighborhood with valid results for concave polygons
- Use Processing Toolbox to run algorithm to generate fixed random points inside polygons (if sampling each neighborhood in multiple different locations)

6. nycnta.json
--------------

This contains the shapefiles for the 195 NTA neighborhoods in NYC, downloaded from https://www1.nyc.gov/site/planning/data-maps/open-data/dwn-nynta.page

 7. ntas.pdf
--------------

This contains the descriptions for the 195 NTA neighborhoods in NYC, downloaded from https://www1.nyc.gov/site/planning/data-maps/open-data/dwn-nynta.

8. index.html
--------------

This contains the code (html, css, js) to create the d3 map visualizations of price and time across NYC

Setup:
- Change variable names and domain to either Percent_Dollar_Diff or Percent_Time_Diff based on desired map (column headers from nyc.csv)
- Uncomment mouseover code for hoverable tooltips over each neighborhood

9. nyc.csv
--------------

This contains the mapping of NTA and Borough Names, as well as the price and time data used by d3 to color the NYC maps

10. nycnta.json
--------------

This contains the shapefiles for the 195 NTA neighborhoods in NYC, downloaded from https://www1.nyc.gov/site/planning/data-maps/open-data/dwn-nynta.page and it is used by d3 to generate the NYC maps
