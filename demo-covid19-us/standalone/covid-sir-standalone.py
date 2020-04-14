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
    # try:
    today = datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
    date = record['date']
    state = record['state']

    try:
        S = float(record['S'])
    except:
        S = float(0)
    
    try:
        I = float(record['I'])
    except:
        I = float(0)
    
    try:
        R = float(record['R'])
    except:
        R = float(0)

    try:
        bed_usage = float(record['bed-usage'])
    except:
        bed_usage = float(0)
    
    try:
        icu_usage = float(record['icu-usage'])
    except:
        icu_usage = float(0)

    try:
        ventilator_usage = float(record['ventilator-usage'])
    except:
        ventilator_usage = float(0)
    
    try:
        hospitalization = float(record['hospitalization'])
    except:
        hospitalization = float(0)

    try:
        icu = float(record['icu'])
    except:
        icu = float(0)

    try:
        ventilator = float(record['ventilator'])
    except:
        ventilator = float(0)

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
                                                'hospitalization' : hospitalization,
                                                'icu' : icu,
                                                'ventilator' : ventilator,
                                                'bed-usage' : bed_usage,
                                                'icu-usage' : icu_usage,
                                                'ventilator-usage' : ventilator_usage  
                                            }
                                        }

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