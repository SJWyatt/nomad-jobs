from influxdb import InfluxDBClient
import pygeohash as pgh
from haversine import haversine, Unit 
import numpy as np

class MapQuery:
    def __init__(self, influx_host, influx_port):
        self.client = InfluxDBClient(host=influx_host, 
                                port=influx_port)
        
        # Dictionary that contains:
        # { 
        #     base_name : [ nearby_county_geohash, etc ... ]
        # }
        self.military_view = self.initialize_military_view()


    def get_military_table_output(self, bases, range_to):
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

        query = "SELECT * FROM covid19 WHERE geohash =~ {0} AND time > '{1}' - 1d".format(expanded_geohash, range_to)
        print(query)
        results = self.client.query(query).get_points()
        print(len(results))

        table_output = []
        for r in results:
            time, confirmed, geohash, location, state = r['time'], r['confirmed'], r['geohash'], r['location'], r['state']
            entry = (time, confirmed, geohash, location, state)
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
