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

measurements = []
measurements_hash = {}

input_file = csv.DictReader(open('/local/data/af_bases.csv'))

for record in input_file:
    today = datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
    name = record['name'].strip()
    # state = record['state'].strip()
    geohash = record['geohash'].strip()
    confirmed = -1 #record[3].strip()
    radius_interest = 50

    measurements_hash[geohash] = {'measurement': 'bases', 
                                                'tags': {}, 
                                                'fields': {}, 
                                                'time': int(today) * 1000 * 1000 * 1000
                                                }

    # measurements_hash[geohash]['tags']['state'] = state.strip()
    measurements_hash[geohash]['tags']['geohash'] = geohash
    measurements_hash[geohash]['tags']['location'] = name
    measurements_hash[geohash]['tags']['radius'] = radius_interest

    # The number needed for the map to display it!
    measurements_hash[geohash]['fields']['confirmed'] = confirmed

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