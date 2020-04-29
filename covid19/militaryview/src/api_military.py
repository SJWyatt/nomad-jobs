import json
import os
import time
import traceback
from datetime import datetime, timedelta, tzinfo
from http import HTTPStatus
from pathlib import Path

import falcon
import numpy as np
import pandas as pd
from falcon.http_status import HTTPStatus

from mapquery import MapQuery
from sirquery import SIRQuery

print("Initalizing military_view...")
start_init = time.time()
INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_PORT = os.environ['INFLUX_DBPORT']
military_view = MapQuery(INFLUX_HOST, INFLUX_PORT)
print(f"Initalized! ({time.time() - start_init:.02f}s)")

print("Initalizing sirquery...")
start_init = time.time()
sir_query = SIRQuery()
print(f"Initalized! ({time.time() - start_init:.02f}s)")

class Server_Check:
    def on_get(self, req, resp):
        string = "OK"
        resp.body = string

    def on_post(self, req, resp):
        string = "OK"
        resp.body = string

class Search:
    def on_post(self, req, resp):
        print("-------------------------------------------")
        print("/search Endpoint...")
        targets = [
            'Infected',
            'Susceptible',
            'Recovered',

            'Confirmed',
            # '14d_Prediction_Map',

            "Hospitalization",
            "ICU",
            "Ventilator",

            # "bed-usage",
            # "icu-usage",
            # "ventilator-usage",
            
            "R0"
        ]

        # return places
        resp.body = json.dumps(targets)

class Query:
    def on_post(self, req, resp):
        print("--------------------------------------------------------------------------------------")
        print("/Query Endpoint...")
        rtn_data = []

        try:
            data = json.load(req.bounded_stream)
            # print("JSON Request:", data)

            scopedVars = data.get('scopedVars', {})
            
            bases = scopedVars.get('Base', {})
            bases = bases.get('value')

            # states = 
            # counties = 
            
            range_to = data.get('range', {}).get('to')

            targets = data['targets']

            # sir_targets = []
            for target in targets:
                if target.get('target', '') == 'Confirmed':
                    military_data = {
                        "columns":[
                            {"text":"time","type":"time"},
                            {"text":"Confirmed","type":"number"},
                            {"text":"geohash","type":"string"},
                            {"text":"location","type":"string"},
                            {"text":"state","type":"string"}
                        ],
                        "rows": [],
                        "type":"table"
                    }
                    military_data['rows'] = military_view.get_military_table_output(bases, range_to)

                    rtn_data.append(military_data)

                elif target.get('target', '') in ['Infected', 'Susceptible', 'Recovered']:
                    geohash_list = military_view.get_nearby_counties(bases, range_to)
                    sir_data = sir_query.get_target(target, geohash_list, range_to)
                    rtn_data.append(sir_data)

                elif target.get('target', '') in ['Hospitalization', 'ICU', 'Ventilator']:
                    geohash_list = military_view.get_nearby_counties(bases, range_to)
                    sir_data = sir_query.get_target(target, geohash_list, range_to)
                    rtn_data.append(sir_data)

                # elif target.get('target', '') in ['bed-usage', 'icu-usage', 'ventilator-usage']:
                #     geohash_list = military_view.get_nearby_counties(bases, range_to)
                #     sir_data = sir_query.get_target(target, geohash_list, range_to)
                #     rtn_data.append(sir_data)

                elif target.get('target', '') == 'R0':
                    geohash_list = military_view.get_nearby_counties(bases, range_to)
                    R0_value = sir_query.get_R0(target, geohash_list, range_to)
                    rtn_data.append(R0_value)
                    # pass

                # elif target.get('target', '') == '14d_Prediction_Map':
                #     query = 'SELECT "infected" AS "Infected" FROM "military_sir" WHERE ("state" =~ /^$States$/ AND "county" =~ /^$County$/) AND time > now() +14d  GROUP BY "geohash", "location"'


        except Exception as e:
            print("Query Exception:", e)
            traceback.print_exc()
        
        resp.body = json.dumps(rtn_data)

class Annotations:
    def on_post(self, req, resp):
        print("-------------------------------------------")
        print("/anotations Endpoint...")
        annot = ""
        try:
            data = json.load(req.bounded_stream)
            # print("JSON Data: ", data)

            range_to = data.get('range', {}).get('to')

            variables = data.get('variables', {})
            bases = variables.get('Base', {})
            bases = bases.get('value')
            
            geohash_list = military_view.get_nearby_counties(bases, range_to)
            annot = sir_query.get_max_infected(geohash_list)
        except Exception as e:
            print("Annotations Exception:",e)
            traceback.print_exc()

        resp.body = json.dumps(annot)

class HandleCORS:
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', 'accept, content-type')

        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, body='\n')


wsgi_app = api = falcon.API(middleware=[HandleCORS()])
app = falcon.API()
app.add_route('/', Server_Check())
app.add_route('/search', Search())
app.add_route('/query', Query())
app.add_route('/annotations', Annotations())

# to start the application run with:
# gunicorn -b 0.0.0.0:5050 api_military:app -w 1 --timeout 10000
print("Ready!")
