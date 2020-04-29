from haversine import haversine, Unit   # pip install haversine
import pandas as pd
import numpy as np

class LocationResolver:
    def __init__(self, online_data_source="https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"):
        self.df = None
        self.locations_map = dict()
        self.initialize(online_data_source)
    
    def get_counties_in_state(self, state):
        return set(self.df[self.df['Province_State'] == state]['Admin2'].to_list())

    def get_expanded_counties_and_states(self, location_hashes):
        location_hashes = self.expand_locations(location_hashes)

        if len(location_hashes) == 1 and location_hashes[0] == 'USA':
            return None, 'USA'

        counties, states = [], []

        for location in location_hashes:
            combined_key = location.split(',')

            # Format: 'state/territory, US'
            # Undefined behavior, we skip for now.
            if len(combined_key) == 2:
                continue

            # Format: 'county, state, US'
            if len(combined_key) == 3:
                counties.append(combined_key[0].strip())
                states.append(combined_key[1].strip())
        
        return counties, states
        

    def expand_locations(self, location_hashes):
        # We ensure no repeated values!
        location_hashes = list(set(location_hashes))

        if len(location_hashes) == 1 and location_hashes[0] == 'US':
            return ['USA']

        new_locations, remove_locations, single_counties = [], [], []
        county_count = 0

        for location in location_hashes:
            combined_key = location.split(',')
            
            # Format: 'state/territory, US'
            # Retrieve all counties within that state.
            if len(combined_key) == 2:
                state = combined_key[0].strip()
                new_counties = self.get_counties_in_state(state)

                for new_county in new_counties:
                    if new_county.startswith('Out of') or new_county.startswith('Unassigned'):
                        continue

                    new_county = "{0}, {1}, {2}".format(new_county, state, 'US')
                    new_locations.append(new_county)
                
                remove_locations.append(location)

            # Format: 'county, state, US'
            if len(combined_key) == 3:
                # Keep a record of which ones were the counties
                # just in case they need smoothing. 
                county_count = county_count + 1
                single_counties.append(location)

        # Removing 'Florida, US' as it's being replaced
        # by each of its counties.
        for location in remove_locations:
            location_hashes.remove(location)

        # Adding each of the new 'Florida, US' counties
        location_hashes.extend(new_locations)

        if county_count < 5:
            new_smoothing_counties = self.find_closest_counties(single_counties)
            location_hashes.extend(new_smoothing_counties)

        expanded_locations = set(location_hashes)
        return expanded_locations

    def find_closest_counties(self, array_of_location_hashes):
        requested_locations_map = dict()
        for location_hash in array_of_location_hashes:            
            if location_hash in self.locations_map.keys():
                requested_locations_map[location_hash] = self.locations_map[location_hash]
        
        # Calculating distances
        location_hash = array_of_location_hashes
        destination_hash = list(self.locations_map.keys())

        rows, cols = (len(location_hash), len(destination_hash))
        distance = [[0 for i in range(cols)] for j in range(rows)] 
        for i in range(rows):
            for j in range(cols):
                distance[i][j] = haversine(requested_locations_map[location_hash[i]], 
                                            self.locations_map[destination_hash[j]]) 

        # Getting new counties
        new_locations_hash = []
        for i in range(rows):
            indices = np.argpartition(distance[i], 4)[:4]
            for index in indices:
                if destination_hash[index] == location_hash[i]:
                    continue
                
                new_locations_hash.append(destination_hash[index])
        
        new_locations_hash = list(set(new_locations_hash))
        return new_locations_hash

    def initialize(self, online_data_source):
        file_exists = False
        try:
            self.df = pd.read_csv(online_data_source)
            file_exists = True
        except:
            print("Could not download file!")
            pass
        else:
            self.df.drop(columns=['UID', 'iso2', 'iso3', 'code3', 'FIPS'])

        if file_exists:
            all_counties = self.df['Admin2'].to_list()
            all_states = self.df['Province_State'].to_list()
            country = np.repeat('US', len(all_counties))
            combined_key = zip(all_counties, all_states, country)

            for item in combined_key:
                location_hash = (', '.join(str(x) for x in item))
                if location_hash.startswith('nan,'):
                    # old_hash = location_hash
                    location_hash = location_hash[5:]

                try:
                    latitude = self.df[self.df['Combined_Key'] == location_hash]['Lat'].to_list()[0]
                    longitude = self.df[self.df['Combined_Key'] == location_hash]['Long_'].to_list()[0]
                    self.locations_map[location_hash] = [latitude, longitude]
                except:
                    pass