import json
import os
import re
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

print("Initalizing military_view...", flush=True)
start_init = time.time()
INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_PORT = os.environ['INFLUX_DBPORT']
military_view = MapQuery(INFLUX_HOST, INFLUX_PORT)
print(f"Initalized! ({time.time() - start_init:.02f}s)", flush=True)

print("Initalizing sirquery...", flush=True)
start_init = time.time()
sir_query = SIRQuery(military_view)
print(f"Initalized! ({time.time() - start_init:.02f}s)", flush=True)

class Server_Check:
    def on_get(self, req, resp):
        resp.body = self.health_check()

    def on_post(self, req, resp):
        resp.body = self.health_check()

    def health_check(self):
        # check if the cached query is older than 1 day.
        last_cached = datetime.now() - sir_query.all_cached_time

        if last_cached > (timedelta(days=1)-timedelta(seconds=1)):
            return "OUTDATED"
        else:
            return "OK"

class Search:
    def on_post(self, req, resp):
        print("-------------------------------------------")
        print("/search Endpoint...", flush=True)
        targets = [
            'Infected',
            'Infected_UB',
            'Infected_LB',
            'Susceptible',
            'Recovered',

            "Active",
            'Confirmed',
            'Deaths',
            # '14d_Prediction_Map',

            'Hospitalization',
            'Hospitalization_UB',
            'Hospitalization_LB',
            'ICU',
            'Ventilator',

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
        print("/Query Endpoint...", flush=True)
        rtn_data = []
        get_all = False

        try:
            data = json.load(req.bounded_stream)
            # print("JSON Request:", data)

            scopedVars = data.get('scopedVars', {})
            
            bases = scopedVars.get('Base', {})
            if bases.get('text', '') == 'All':
                get_all = True
            bases = bases.get('value')

            # number of days to forcast (for the prediction map.)
            # forecast = scopedVars.get('Forcast', {})
            # forecast = forecast.get('value')

            # # set default of +14 days prediction
            # pred_range = datetime.now().replace(hour=23, minute=59, second=59, microsecond=59) + timedelta(days=14))
            # # convert +1d, +2d, into a datetime object.
            # try:
            #     plus_minus = forecast[0]
            #     time_variable = forecast[-1]
            #     shift_days = int(re.sub("[^0-9]", "", forecast))
            #     pred_range = datetime.now().replace(hour=23, minute=59, second=59, microsecond=59) + timedelta(days=shift_days)
            # except Exception:
            #     print("Cannot convert Forecast Value to date!", flush=True)

            # get states and counties... (for backwards compatibility)
            # states = scopedVars.get('State', {}).get('value')
            # counties = scopedVars.get('County', {}).get('value')
            
            range_to = data.get('range', {}).get('to')

            targets = data['targets']

            # sir_targets = []
            for target in targets:
                if target.get('target', '') in ['Confirmed', 'Deaths']:
                    military_data = {
                        "columns":[
                            {"text":"time","type":"time"},
                            {"text":target['target'],"type":"number"},
                            {"text":"geohash","type":"string"},
                            {"text":"location","type":"string"},
                            {"text":"state","type":"string"}
                        ],
                        "rows": [],
                        "type":"table"
                    }
                    military_data['rows'] = military_view.get_military_table_output(bases, range_to, target['target'])

                    rtn_data.append(military_data)

                elif target.get('target', '') == "Active":
                    try:
                        active_cases = military_view.get_active_cases(bases, range_to, target)
                        rtn_data.append(active_cases)
                    except Exception as e:
                        print("Exception:", e)
                        traceback.print_exc()
                        print("", end='', flush=True)

                elif target.get('target', '') in ['Infected', 'Susceptible', 'Recovered']:
                    if get_all:
                        sir_data = sir_query.get_target(target, geohash_list="All", range_to=range_to)
                        rtn_data.append(sir_data)
                    else:
                        geohash_list = military_view.get_nearby_counties(bases, range_to)
                        sir_data = sir_query.get_target(target, geohash_list, range_to)
                        rtn_data.append(sir_data)

                elif target.get('target', '') in ["Infected_UB", "Infected_LB", 'Hospitalization_UB', 'Hospitalization_LB']:
                    if get_all:
                        sir_data = sir_query.get_target(target, geohash_list="All", range_to=range_to)
                        rtn_data.append(sir_data)
                    else:
                        geohash_list = military_view.get_nearby_counties(bases, range_to)
                        sir_data = sir_query.get_target(target, geohash_list, range_to)
                        rtn_data.append(sir_data)

                elif target.get('target', '') in ['Hospitalization', 'ICU', 'Ventilator']:
                    if get_all:
                        sir_data = sir_query.get_target(target, geohash_list="All", range_to=range_to)
                        rtn_data.append(sir_data)
                    else:
                        geohash_list = military_view.get_nearby_counties(bases, range_to)
                        sir_data = sir_query.get_target(target, geohash_list, range_to)
                        rtn_data.append(sir_data)

                # elif target.get('target', '') in ['bed-usage', 'icu-usage', 'ventilator-usage']:
                #     geohash_list = military_view.get_nearby_counties(bases, range_to)
                #     sir_data = sir_query.get_target(target, geohash_list, range_to)
                #     rtn_data.append(sir_data)

                # elif target.get('target', '') in ['bed-usage', 'icu-usage', 'ventilator-usage']:
                #     geohash_list = military_view.get_nearby_counties(bases, range_to)
                #     sir_data = sir_query.get_target(target, geohash_list, range_to)
                #     rtn_data.append(sir_data)

                # elif target.get('target', '') in ['bed-usage', 'icu-usage', 'ventilator-usage']:
                #     geohash_list = military_view.get_nearby_counties(bases, range_to)
                #     sir_data = sir_query.get_target(target, geohash_list, range_to)
                #     rtn_data.append(sir_data)

                elif target.get('target', '') == 'R0':
                    if get_all:
                        R0_value = sir_query.get_R0(target, geohash_list="All", range_to=range_to)
                        rtn_data.append(R0_value)
                    else:
                        geohash_list = military_view.get_nearby_counties(bases, range_to)
                        R0_value = sir_query.get_R0(target, geohash_list, range_to)
                        rtn_data.append(R0_value)

                # elif target.get('target', '') == '14d_Prediction_Map':
                #     query = 'SELECT "infected" AS "Infected" FROM "military_sir" WHERE ("state" =~ /^$States$/ AND "county" =~ /^$County$/) AND time > now() +14d  GROUP BY "geohash", "location"'


        except Exception as e:
            print("Query Exception:", e)
            traceback.print_exc()
        
        resp.body = json.dumps(rtn_data)

class Annotations:
    def on_post(self, req, resp):
        print("-------------------------------------------")
        print("/anotations Endpoint...", flush=True)
        annot = ""
        get_all = False
        try:
            data = json.load(req.bounded_stream)
            # print("JSON Data: ", data)

            range_to = data.get('range', {}).get('to')

            variables = data.get('variables', {})
            bases = variables.get('Base', {})
            if bases.get('text', '') == 'All':
                get_all = True
            bases = bases.get('value')
            
            if get_all:
                annot = sir_query.get_max_infected(geohash_list="All")
            else:
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
print("Ready!", flush=True)
