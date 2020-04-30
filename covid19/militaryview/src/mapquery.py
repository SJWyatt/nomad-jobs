from influxdb import InfluxDBClient
import pygeohash as pgh
from haversine import haversine, Unit 
import numpy as np
from datetime import datetime, timedelta, tzinfo

class MapQuery:
    def __init__(self, influx_host, influx_port):
        self.client = InfluxDBClient(host=influx_host, 
                                port=influx_port)
        
        # Dictionary that contains:
        # { 
        #     base_name : [ nearby_county_geohash, etc ... ]
        # }
        self.military_view = self.initialize_military_view()


    def get_military_table_output(self, bases, range_to, target="Confirmed"):
        self.client.switch_database('covid19')
        allowed_geohashes = []

        for base_name, geohash_list in self.military_view.items():
            if base_name in bases:
                allowed_geohashes.extend(geohash_list)
        
        # Creating Regexp for all of the geohashes.
        expanded_geohash = "/^("
        for i in range(len(allowed_geohashes)):
            expanded_geohash = expanded_geohash + allowed_geohashes[i]
            if i != len(allowed_geohashes) - 1:
                expanded_geohash = expanded_geohash + "|"

        expanded_geohash = expanded_geohash + ")$/"

        # Creating time constraints

        query = "SELECT * FROM covid19 WHERE geohash =~ {0} AND time > '{1}' - 2d".format(expanded_geohash, range_to)
        print(query)
        results = self.client.query(query).get_points()

        table_output = []
        for r in results:
            time, data, geohash, location, state = r['time'], r[target.lower()], r['geohash'], r['location'], r['state']
            entry = (time, data, geohash, location, state)
            table_output.append(entry)

        return table_output

    def get_nearby_counties(self, bases, range_to):
        self.client.switch_database('covid19')
        allowed_geohashes = []

        for base_name, geohash_list in self.military_view.items():
            if base_name in bases:
                allowed_geohashes.extend(geohash_list)

        return allowed_geohashes

    def get_military_table_output_1(self):
        self.client.switch_database('covid19')
        allowed_geohashes = []

        for _, geohash_list in self.military_view.items():
            allowed_geohashes.extend(geohash_list)
        
        # Creating Regexp for all of the geohashes.
        expanded_geohash = "/^("
        for i in range(len(allowed_geohashes)):
            expanded_geohash = expanded_geohash + allowed_geohashes[i]
            if i != len(allowed_geohashes) - 1:
                expanded_geohash = expanded_geohash + "|"

        expanded_geohash = expanded_geohash + ")$/"
        query = "SELECT * FROM covid19 WHERE geohash =~ {0} AND time > now() - 2d".format(expanded_geohash)
        results = self.client.query(query).get_points()

        table_output = []
        for r in results:
            time, confirmed, geohash, location, state = r['time'], r['confirmed'], r['geohash'], r['location'], r['state']
            entry = (time, confirmed, geohash, location, state)
            table_output.append(entry)

        return table_output

    def get_active_cases(self, bases, range_to, target):
        self.client.switch_database('covid19')
        allowed_geohashes = []

        for base_name, geohash_list in self.military_view.items():
            if base_name in bases:
                allowed_geohashes.extend(geohash_list)
        
        # Creating Regexp for all of the geohashes.
        expanded_geohash = "/^("
        for i in range(len(allowed_geohashes)):
            expanded_geohash = expanded_geohash + allowed_geohashes[i]
            if i != len(allowed_geohashes) - 1:
                expanded_geohash = expanded_geohash + "|"

        expanded_geohash = expanded_geohash + ")$/"

        # Creating time constraints

        query = "SELECT * FROM covid19 WHERE geohash =~ {0} AND time > '{1}' - 2d".format(expanded_geohash, range_to)
        # print(query)
        results = self.client.query(query).get_points()

        cases_output = []
        for r in results:
            time, confirmed, geohash, location, state = r['time'], r['Confirmed'], r['geohash'], r['location'], r['state']
            entry = (time, confirmed, geohash, location, state)
            cases_output.append(entry)

        data = []
        dates = []
        first_time = datetime.strptime(cases_output[0][0], "%Y-%m-%dT%H:%M:%S.%fZ")
        ii = 0
        for time, confirmed, geohash, location, state in cases_output:
            # ignore the first 14 days
            if (time - first_time) > timedelta(days=14):
                data.append(confirmed - cases_output[ii][0])
                ii+=1
                dates.append(datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%m/%d/%Y'))
            else:
                data.append(0)
                dates.append(datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%m/%d/%Y'))

        return self.format_as_timeseries(data, dates, target)

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

    def to_epoch(self, dt_format):
        epoch = int((datetime.strptime(dt_format, "%Y-%m-%dT%H:%M:%S.%fZ") - datetime(1970, 1, 1)).total_seconds()) * 1000
        return epoch

    def initialize_military_view(self):
        # Getting all geohashes 
        self.client.switch_database('covid19')
        get_geohashes = "SHOW TAG VALUES with KEY=geohash"
        results = self.client.query(get_geohashes).get_points()
        geohashes = [result['value'] for result in results]
        geohashes = np.array(geohashes)

        # Getting all Bases
        self.client.switch_database('bases')
        results = self.client.query(get_geohashes).get_points()
        bases_geohashes = [result['value'] for result in results]
        bases_geohashes = np.array(bases_geohashes)

        # Mapping Name --> Geohash
        query = "SELECT * FROM bases"
        results = self.client.query(query).get_points()
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
        
        return geohash_map

# if __name__ == "__main__":
#     mq = MapQuery('172.31.80.76', 8086)
#     print(mq.initialize_military_view())
