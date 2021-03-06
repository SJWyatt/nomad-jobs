import json
import math
import os
import time
import traceback
from datetime import datetime, timedelta, tzinfo

import numpy as np
import pandas as pd
from haversine import Unit, haversine

# import geohash
import geohash2
from LocationResolver import LocationResolver
from sir import calculate_sir


class SIRQuery:
    def __init__(self):
        # constants
        self.millnames = ['',' K',' Mil',' Bil',' Tril']

        self.prev_sir_model = {}
        self.prev_location_hash = []


        self.initialize()

    def get_sir_model(self, geohash_list):
        location_hash = []
        counties = []
        states = []

        for geohash in geohash_list:
            loc_hash = self.location_data['geohashes'].get(geohash)
            if loc_hash is not None:
                location_hash.append(loc_hash)
            else: 
                print("Cannot find", geohash, "in list of known geohashes!")

        if len(location_hash) != 0 and location_hash == self.prev_location_hash:
            # reuse previous data
            print("Reusing previous data...")

        elif len(location_hash) != 0:
            # print("Locations: ", location_hash)
            try:
                counties, states = self.geo.get_expanded_counties_and_states(location_hash)
            except Exception:
                print("Cannot get locations, getting old fasioned way...")
                # print("Recieved:", geohash_list)
                # print("Locations:", location_hash)
                for loc_hash in location_hash:
                    try:
                        state, county, _, _, _ = self.location_data['locations'][loc_hash]
                        states.append(state)
                        counties.append(county)
                    except AttributeError:
                        pass

            try:
                start_sir = time.time()
                
                self.prev_sir_model, self.prev_R0 = calculate_sir(counties, states)
                self.prev_sir_model = self.prev_sir_model.dropna()

                # save location hash for next time.
                self.prev_location_hash = location_hash
                print(f"INFO: calculate_sir took {time.time() - start_sir:.02f}s")
            except IndexError:
                print("---- Not Enough data to calculate sir model! ----")
                raise ValueError("Not Enough data to calculate sir model!")
            except Exception as e:
                raise Exception(e)
        else:
            print("Error: No locations found!")
            # return 
        
        # return self.get_target(target, range_to)

    def get_target(self, target, geohash_list, range_to):
        # Load the model for this location
        self.get_sir_model(geohash_list)

        # format the data for this target
        target_data = {}
        if target.get('type') == 'timeseries':
            dates = self.prev_sir_model['date'].tolist()
            data = []
            if target.get('target') == 'Susceptible':
                data = self.prev_sir_model['S'].to_list()
                target_data = self.format_as_timeseries(data, dates, target['target'])
            elif target.get('target') == 'Infected':
                data = self.prev_sir_model['I'].to_list()
                target_data = self.format_as_timeseries(data, dates, target['target'])
            elif target.get('target') == 'Recovered':
                data = self.prev_sir_model['R'].to_list()
                target_data = self.format_as_timeseries(data, dates, target['target'])
            elif target.get('target') == 'R0':
                target_data = self.format_as_timeseries([self.prev_R0], [datetime.now().strftime("%m/%d/%Y")], target['target'])

        elif target.get('type') == 'table':
            print("Cannot format as Table Yet!")
            pass

        return target_data

    def get_R0(self, target, geohash_list, range_to):
        self.get_sir_model(geohash_list)

        target_data = {}
        if target.get('type') == 'timeseries' and target.get('target') == 'R0':
            target_data = self.format_as_timeseries([self.prev_R0], [datetime.now().strftime("%m/%d/%Y")], target['target'])

        return target_data

    def get_usage_data(self):
        pass

    def get_max_infected(self, geohash_list):
        self.get_sir_model(geohash_list)

        annotations = []
        try: 
            max_point = self.prev_sir_model['I'].idxmax()
            print("Max Point:", max_point)
            
            max_val = self.prev_sir_model['I'].max()
            print("Max:", max_val)
            
            max_time = self.prev_sir_model['date'][max_point]
            print("Max Time:", max_time)
            
            date_obj = datetime.strptime(max_time, '%m/%d/%Y').replace(hour=23, minute=59, second=59, microsecond=59)

            # timestamp = datetime.now()
            annotations.append({
                "text": "The Peak Infection Rate for Covid-19 \n(%s)"%(self.millify(max_val)),
                "Title": "Peak Infection Rate",
                "time": self.to_epoch(date_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                # "time": to_epoch(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
                # "isRegion": False,
                # "timeEnd": timestamp_end,
                # "tags": ["tag1", "tag2"]
            })
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            
        return annotations

    def format_as_table(self, sir_data):
        pass

    def format_as_timeseries(self, sir_data, dates, target):
        target_data = {
            'target': target,
            'datapoints': [],
            'type': 'timeseries'
        }

        ii = 0
        for row in sir_data:
            date_obj = datetime.strptime(dates[ii], '%m/%d/%Y').replace(hour=23, minute=59, second=59, microsecond=59)

            # if date_obj >= datetime_from and date_obj < datetime_to:
            target_data['datapoints'].append([row, self.to_epoch(date_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))])
            
            ii+=1

        return target_data

    def to_epoch_mdy(self, dt_format):
        epoch = int((datetime.strptime(dt_format, "%m-%d-%Y") - datetime(1970, 1, 1)).total_seconds()) * 1000
        return epoch

    def to_epoch(self, dt_format):
        epoch = int((datetime.strptime(dt_format, "%Y-%m-%dT%H:%M:%S.%fZ") - datetime(1970, 1, 1)).total_seconds()) * 1000
        return epoch

    def millify(self, n):
        n = float(n)
        millidx = max(0,min(len(self.millnames)-1,
                            int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

        return '{:.02f}{}'.format(n / 10**(3 * millidx), self.millnames[millidx])

    def save_state_data(self, county_wise_filepath):
        """ Data is formatted in the following way
        self.location_data = {
            "geohashes" : {
                "geohash": "location_hash"
            },
            "locations": {
                "location_hash": [state, county, country, geohash, fips]
            }
        }
        """
        self.location_data = {
            "geohashes": {},
            "locations": {}
        }

        # load the data
        self.csv_data = pd.read_csv(county_wise_filepath, delimiter=',', index_col=[0], parse_dates=[0])
        
        for _, row in self.csv_data.iterrows():
            # only store unique data
            if self.location_data['locations'].get(row['Combined_Key']) is None:
                location_hash = row['Combined_Key']
                state = row['Province_State']
                county = row['Admin2']
                country = row['Country_Region']
                fips = row['FIPS']

                county_geohash = ''
                try:
                    lat = ''
                    try:
                        lat = float(row['Lat'].strip())
                    except AttributeError:
                        lat = float(row['Lat'])

                    log = ''
                    try:
                        log = float(row['Long_'].strip())
                    except AttributeError:
                        log = float(row['Long_'])

                    county_geohash = geohash2.encode(lat,log) # Generate Geohash for use with Grafana Plugin
                except Exception as e:
                    print("Error Getting Geohash: ", e)
                    # traceback.print_exc()

                if county_geohash != '':
                    self.location_data['geohashes'][county_geohash] = location_hash
                else:
                    print("Empty Geohash! (",location_hash,")")

                self.location_data['locations'][location_hash] = [state, county, country, county_geohash, fips]

    def initialize(self):
        
        current_dir = os.getcwd()
        # SIR_FILE_PATH = current_dir+"/Data/sir_model.csv"
        # SIR_FOLDER_PATH = current_dir+"/Data/states/"
        USA_COUNTY_WISE_PATH = current_dir+"/Data/covid_kaggle/usa_county_wise.csv"
        # USAGE_DATA_PATH = current_dir+"/Data/resource_usage.csv"
        # STATE_DATA_PATH = current_dir+"/Data/full_state_sir.csv"

        # print("Loading SIR .csv's")
        # cache csv data
        # self.sir_Data = pd.read_csv(SIR_FILE_PATH, delimiter=',')
        # # self.csv_data = None
        # self.usage_data = pd.read_csv(USAGE_DATA_PATH, delimiter=',')
        # self.state_data = pd.read_csv(STATE_DATA_PATH, delimiter=',')
        # self.state_data['date'] = pd.to_datetime(self.state_data['date'])
        # self.state_data['date'] = np.asarray([self.to_epoch_mdy(thetime.strftime("%m-%d-%Y")) for thetime in self.state_data['date']])
        # print("Finished!")

        print("Loading State Dict...")
        # get state data
        self.save_state_data(USA_COUNTY_WISE_PATH)
        print("Finished!")

        print("Loading Geo...")
        # get geo data
        self.geo = LocationResolver()
        print("Finished!")
