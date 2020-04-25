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
INFLUX_PORT =  os.environ['INFLUX_DBPORT']
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
            # print("Request: ",request)
            data = json.load(req.bounded_stream)
            print("JSON Request:", data)

            # fromDate = data['range']['from']
            # toDate = data['range']['to']
            # interval = data['intervalMs']
            # maxPoints = data['maxDataPoints']

            scopedVars = data.get('scopedVars', {})
            state = scopedVars.get('States', {})
            county = scopedVars.get('County', {})

            states = state.get('value', 'All')
            counties = county.get('value', 'All')

            
            if state.get('text', 'All') == 'All':
                states = 'All'

            if county.get('text', 'All') == 'All':
                counties = None

            # targets = data['targets']
            
            # print("Get data from %s to %s"%(fromDate, toDate))
            # print("%d number of points at %dms intervals."%(maxPoints, interval))
            print("States:", states, "Counties:",counties)
            # print("Targets",targets)

            # stats = get_data(fromDate, toDate, maxPoints, interval, states, counties, targets)

            # ignore what the user says they want, we're giving them what we want to.
            # military_data = [{
            #     # 'name':"Covid19 Military View",
            #     "columns":[
            #         "time",
            #         "Confirmed",
            #         "geohash",
            #         "location",
            #         "state"
            #     ],
            #     "rows": [],
            #     "type":"table"
            # }]
            # military_data[0]['rows'] = military_view.get_military_table_output()

            military_data = [{
                # 'name':"Covid19 Military View",
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
            military_data[0]['rows'] = military_view.get_military_table_output()

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