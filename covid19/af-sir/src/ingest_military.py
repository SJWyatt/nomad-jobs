#!/usr/bin/python3
import csv
import itertools
import os
import time
import traceback
from datetime import datetime, timedelta, tzinfo
from tqdm import tqdm

from haversine import Unit, haversine
import numpy as np
import requests
import pygeohash as pgh
from influxdb import InfluxDBClient

from sirquery import SIRQuery

start_time = time.time()

INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_DB = os.environ['INFLUX_DB']
INFLUX_DBPORT =  os.environ['INFLUX_DBPORT']
INFLUX_USER = os.environ['INFLUX_USER']
INFLUX_PASS = os.environ['INFLUX_PASS']
INFLUX_DROPMEASUREMENT = True # True

client = InfluxDBClient(INFLUX_HOST, INFLUX_DBPORT, INFLUX_USER, INFLUX_PASS, INFLUX_DB)

def to_epoch_mdy(dt_format):
    epoch = int((datetime.strptime(dt_format, "%m/%d/%Y").replace(hour=23, minute=59, second=59, microsecond=59) - datetime(1970, 1, 1)).total_seconds()) * 1000
    return epoch

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

GMT = Zone(0, False, 'GMT')

print("Getting data...")
measurements = []
measurements_hash = {}

print("Initalizing sirquery...")
start_init = time.time()
sir_query = SIRQuery()
print(f"Initalized! ({time.time() - start_init:.02f}s)")

print("Processing data...")

# Getting all Geohashes
client.switch_database('covid19')
get_geohashes = "SHOW TAG VALUES with KEY=geohash"
results = client.query(get_geohashes).get_points()
geohashes = [result['value'] for result in results]
geohashes = np.array(geohashes)

# Getting all Bases
client.switch_database('bases')
results = client.query(get_geohashes).get_points()
bases_geohashes = [result['value'] for result in results]
bases_geohashes = np.array(bases_geohashes)

# Mapping Name --> Geohash
query = "SELECT * FROM bases"
results = client.query(query).get_points()
geohash_to_location = {}
for r in results:
    geohash, location = r['geohash'], r['location']
    geohash_to_location[geohash] = location

# Calculating distances between all bases and counties.
rows, cols = len(bases_geohashes), len(geohashes)
distance = [[0 for i in range(cols)] for j in range(rows)] 
for i in range(rows):
    x = pgh.decode(bases_geohashes[i])
    for j in range(cols):
        y = pgh.decode(geohashes[j])
        distance[i][j] = haversine(x, y, unit=Unit.MILES) 
distance = np.array(distance)

# Creating a dictionary 
# {base_name : [ geohash_county_1, gh_county_2 ... ]}
geohash_map = {}
for i in range(rows):
    indices = np.argwhere(distance[i] < 50).flatten()
    geohash_map[geohash_to_location[bases_geohashes[i]]] = geohashes[indices]

start_storing = time.time()
# only use data for the next 15 days
today_date = datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).strftime("%m/%d/%Y")
future_date = (datetime.today().replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT) + timedelta(days=15)).strftime("%m/%d/%Y")

# print("Sir Model:", sir_model[included_dates].head())

for af_base in tqdm(geohash_map, "Getting Bases..."):
    # print("Base:", af_base, "GeoHashes:", geohash_map[af_base])
    for county_geohash in geohash_map[af_base]:
        print(county_geohash, " -> ", sir_query.location_data['geohashes'].get(county_geohash))

        try:
            sir_query.get_sir_model([county_geohash])
        except ValueError:
            continue
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            continue

        sir_model = sir_query.prev_sir_model

        try:
            included_dates = (sir_model['date'] > today_date) & (sir_model['date'] <= future_date)

            location_hash = sir_query.location_data['geohashes'].get(county_geohash)

            state, county, country, _, fips = sir_query.location_data['locations'][location_hash]

            # save all predictions from today till 14 days in the future.
            for _, row in sir_model[included_dates].iterrows():
                datemdy = datetime.strptime(row['date'], '%m/%d/%Y').replace(hour=23, minute=59, second=59, microsecond=59).replace(tzinfo=GMT).timestamp()
                time_loc_hash = "{}:{}".format(datemdy, location_hash)

                if time_loc_hash not in measurements_hash and county_geohash != '': 
                    measurements_hash[time_loc_hash] = {'measurement': INFLUX_DB, 
                                                        'tags': {}, 
                                                        'fields': {}, 
                                                        'time': int(datemdy) * 1000 * 1000 * 1000
                                                        }

                    measurements_hash[time_loc_hash]['tags']['location'] = location_hash
                    measurements_hash[time_loc_hash]['tags']['country'] = country
                    measurements_hash[time_loc_hash]['tags']['state'] = state.strip()
                    measurements_hash[time_loc_hash]['tags']['county'] = county.strip()
                    measurements_hash[time_loc_hash]['tags']['geohash'] = county_geohash
                    measurements_hash[time_loc_hash]['tags']['fips'] = fips
                    measurements_hash[time_loc_hash]['tags']['base'] = af_base

                    try:
                        measurements_hash[time_loc_hash]['fields']['susceptible'] = int(row['S'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['susceptible'] = 0
                    
                    try:
                        measurements_hash[time_loc_hash]['fields']['infected'] = int(row['I'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['infected'] = 0

                    try:
                        measurements_hash[time_loc_hash]['fields']['recovered'] = int(row['R'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['recovered'] = 0

                    try:
                        measurements_hash[time_loc_hash]['fields']['hospitalization'] = int(row['hospitalization'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['hospitalization'] = 0

                    try:
                        measurements_hash[time_loc_hash]['fields']['icu'] = int(row['icu'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['icu'] = 0

                    try:
                        measurements_hash[time_loc_hash]['fields']['ventilator'] = int(row['ventilator'])
                    except ValueError:
                        measurements_hash[time_loc_hash]['fields']['ventilator'] = 0

            print(f"rearranging data took {time.time() - start_storing:.02f}s")
        except KeyError:
            print("SIR Model KeyError!!!")
            traceback.print_exc()

print("Done processing data!")

# display the first measurement
for key in measurements_hash:
    print("Measurement[%s]:"%(key,), measurements_hash[key])
    break

print("Preparing for data ingest...")
# create database (does nothing if already exists)
client.create_database(INFLUX_DB)
client.switch_database(INFLUX_DB)

# Drop existing Measurement to ensure data consistency with Datasource being updated regularly
if INFLUX_DROPMEASUREMENT:
    client.drop_measurement(INFLUX_DB)

#Iterate through Hash table and format for Influxdb Client
for m in measurements_hash:
    measurements.append(measurements_hash[m])

print("measurements[0]:", measurements[0])

#Commit to Influxdb
if measurements:    
    client.write_points(measurements, batch_size=1000)

print("Done ingesting data!")


print(f"Total time was {time.time() - start_time:.02f}s")