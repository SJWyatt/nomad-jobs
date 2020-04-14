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


INFLUX_HOST = "localhost"
INFLUX_DB = "sir"
INFLUX_DBPORT =  8086
INFLUX_USER = ""
INFLUX_PASS = ""
INFLUX_DROPMEASUREMENT = True

client = InfluxDBClient(INFLUX_HOST, INFLUX_DBPORT,INFLUX_USER,INFLUX_PASS, INFLUX_DB)
GMT = Zone(0, False, 'GMT')

measurements = []
measurements_hash = {}

print("Processing data...")

wrapper = csv.DictReader(open('sir_model.csv'))
results = []
for record in wrapper:
    try:
        today = datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
        date = record['date']
        state = record['state']
        S = float(record['S'])
        I = float(record['I']) 
        R = float(record['R'])
        hospitalization = record['hospitalization'] 
        icu = record['icu']
        ventilator = record['ventilator'] 
        datemdy = datetime.strptime(date, '%m/%d/%Y').replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
        time_loc_hash = "{}:{}".format(datemdy, state)  
        measurements_hash[time_loc_hash] = { 'measurement' : 'sir',
                                                'tags' : {
                                                    'state': str(state)
                                                },
                                                'time' : int(datemdy) * 1000 * 1000 * 1000,
                                                'fields': {
                                                    'S' : S,
                                                    'I' : I,
                                                    'R' : R,
                                                    'hospitalization' : float(hospitalization),
                                                    'icu' : float(icu),
                                                    'ventilator' : float(ventilator) 
                                                }
                                            }
    except:
        print("Skipping record...")

print("Done processing data!")

print("Preparing for data ingest...")
#Drop existing Measurement to ensure data consistency with Datasource being updated regularly
if INFLUX_DROPMEASUREMENT:
    client.drop_measurement('sir')
#Iterate through Hash table and format for Influxdb Client
for m in measurements_hash:
    measurements.append(measurements_hash[m])   

#print(measurements)
# Commit to Influxdb
if measurements:    
    client.write_points(measurements, batch_size=1000)

print("Done ingesting data!")