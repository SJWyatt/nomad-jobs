import csv
import requests
import itertools
import geohash
from datetime import datetime, tzinfo, timedelta
from influxdb import InfluxDBClient
import os

class Zone(tzinfo):
    def __init__(self, offset, isdst, name):
        self.offset = offset
        self.isdst = isdst
        self.name = name

    def utcoffset(self, dt):
        return timedelta(hours=self.offset) + self.dst(dt)

    def dst(self, dt):
        return timedelta(hours=1) if self.isdst else timedelta(0)

    def tzname(self, dt):
        return self.name


INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_DB = os.environ['INFLUX_DB']
INFLUX_DBPORT =  os.environ['INFLUX_DBPORT']
INFLUX_USER = os.environ['INFLUX_USER']
INFLUX_PASS = os.environ['INFLUX_PASS']
INFLUX_DROPMEASUREMENT = True

client = InfluxDBClient(INFLUX_HOST, INFLUX_DBPORT,INFLUX_USER,INFLUX_PASS, INFLUX_DB)
GMT = Zone(0, False, 'GMT')

print("Downloading data...")
#Iterate through each Source File and build hash table

inputfiles = {
    "confirmed":"https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv",
    "deaths":"https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"
}
measurements = []
measurements_hash = {}

print("Processing data...")
#Iterate through each Source File and build hash table
for i in sorted(inputfiles.keys()):
    field = i
    url = inputfiles[i]
    response = requests.get(url)
    if response.status_code != 200:
        print('Failed to get data:', response.status_code)
    else:
        wrapper = csv.DictReader(response.text.strip().split('\n'))
        results = []
        for record in wrapper:
            today = datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
            country = record['Country_Region'].strip()
            state = record['Province_State'].strip()
            county = record['Admin2'].strip()    
            location_hash = record['Combined_Key'].strip()
            fips = record['FIPS'].strip()

            if not fips:
                continue

            try:
                lat = float(record['Lat'].strip())
                lon = float(record['Long_'].strip())
            except:
                continue

            if field == "confirmed":
                datekeys = len(record) - 11
            elif field == "deaths":
                # Deaths has an extra Population record
                datekeys = len(record) - 12 
                population = float(record['Population'].strip())

            for k in sorted(record.keys())[:datekeys]:    
                datemdy = datetime.strptime(k, '%m/%d/%y').replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
                time_loc_hash = "{}:{}".format(datemdy, location_hash)  

                if time_loc_hash not in measurements_hash: 
                    measurements_hash[time_loc_hash] = {'measurement': 'covid19', 
                                                        'tags': {}, 
                                                        'fields': {}, 
                                                        'time': int(datemdy) * 1000 * 1000 * 1000
                                                        }

                    measurements_hash[time_loc_hash]['tags']['location'] = location_hash
                    measurements_hash[time_loc_hash]['tags']['country'] = country
                    measurements_hash[time_loc_hash]['tags']['state'] = state.strip()
                    measurements_hash[time_loc_hash]['tags']['county'] = county.strip()
                    measurements_hash[time_loc_hash]['tags']['geohash'] = geohash.encode(lat,lon) # Generate Geohash for use with Grafana Plugin
                    measurements_hash[time_loc_hash]['tags']['fips'] = fips

                try:
                    measurements_hash[time_loc_hash]['fields'][field] = int(record[k]) 
                except ValueError:
                    measurements_hash[time_loc_hash]['fields'][field] = 0    
                
                try:
                    if field == "deaths":
                        measurements_hash[time_loc_hash]['fields']['population'] = population
                except ValueError:
                    measurements_hash[time_loc_hash]['fields']['population'] = 0 

print("Done processing data!")

print("Preparing for data ingest...")
#Drop existing Measurement to ensure data consistency with Datasource being updated regularly
if INFLUX_DROPMEASUREMENT:
    client.drop_measurement(INFLUX_DB)
#Iterate through Hash table and format for Influxdb Client
for m in measurements_hash:
    measurements.append(measurements_hash[m])   
#Commit to Influxdb
if measurements:    
    client.write_points(measurements, batch_size=1000)

print("Done ingesting data!")