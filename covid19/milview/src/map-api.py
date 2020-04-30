#!/usr/bin/python3
import falcon
from falcon.http_status import HTTPStatus
import uuid
from http import HTTPStatus
from pathlib import Path
import os
import time
import numpy as np
from datetime import datetime, timedelta, tzinfo
import traceback
import json
from mapquery import MapQuery

INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_PORT = os.environ['INFLUX_DBPORT']
military_view = MapQuery(INFLUX_HOST, INFLUX_PORT)

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
            # 'Infected',
            # 'Susceptible',
            # 'Recovered',
            'Confirmed'
        ]

        # return places
        resp.body = json.dumps(targets)

class Query:
    def on_post(self, req, resp):
        print("--------------------------------------------------------------------------------------")
        print("/Query Endpoint...")
        military_data = {}

        try:
            data = json.load(req.bounded_stream)
            print("JSON Request:", data)

            scopedVars = data.get('scopedVars', {})
            bases = scopedVars.get('Base', {})
            bases = bases.get('value')
            range_to = data.get('range', {}).get('to')

            military_data = [{
                "columns":[
                    {"text":"time","type":"time"},
                    {"text":"Confirmed","type":"number"},
                    {"text":"geohash","type":"string"},
                    {"text":"location","type":"string"},
                    {"text":"state","type":"string"}
                ],
                "rows": [],
                "type":"table"
            }]
            military_data[0]['rows'] = military_view.get_military_table_output(bases, range_to)

        except Exception as e:
            print("Query Exception:", e)
            traceback.print_exc()
        
        resp.body = json.dumps(military_data)


class HandleCORS:
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', 'POST')
        resp.set_header('Access-Control-Allow-Headers', 'accept, content-type')

        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200, body='\n')


wsgi_app = api = falcon.API(middleware=[HandleCORS()])
app = falcon.API()
app.add_route('/', Server_Check())
app.add_route('/search', Search())
app.add_route('/query', Query())


# start the application
# app.run(host='0.0.0.0')
# Run with gunicorn -b 0.0.0.0:5050 map-api:app -w 1 --timeout 10000
print("Ready!")