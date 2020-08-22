#!/usr/bin/env python
# coding=utf-8
#
# Copyright © 2011-2015 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function
import os,sys
import time
import requests
import json

splunkhome = os.environ['SPLUNK_HOME']
sys.path.append(os.path.join(splunkhome, 'etc', 'apps', 'searchcommands_app', 'lib'))
from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option, validators

class GraphQLClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.token = None
        self.headername = None

    def execute(self, query, variables=None):
        resp = self.self._send(query, variables)
        if resp is not None:
            if resp.status_code < 300:
               return resp.content
        

    def inject_token(self, token, headername='Authorization'):
        self.token = token
        self.headername = headername

    def _send(self, query, variables):
        data = {'query': query,
                'variables': variables}
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        if self.token is not None:
            headers[self.headername] = '{}'.format(self.token)

        try:
            #response = urllib.request.urlopen(req)
            #req = urllib.request.Request(self.endpoint, json.dumps(data).encode('utf-8'), headers)
            response = requests.post(self.endpoint, json=data, headers=headers, verify=False)
            
            return response
        except Exception as e:
            print(str(e))            
            raise e

    def http_execute(self, query, variables=None):
        return self._send(query, variables)

@Configuration(type='events', retainsevents=True, streaming=False)
class GraphQLQuery(GeneratingCommand):
    query = Option(require=True,doc='''
        **Syntax:** **query=***<graphql query>*
        **Description:** The graphql query to run.''',)

    event_per_result = Option(
        doc='''
        **Syntax:** **event_per_result=***<true/false>*
        **Description:** Create an event per table result.''',
        require=False, validate=validators.Boolean())

    def generate(self):
        query = self.query
        event_per_result = self.event_per_result
        self.logger.debug("Running GQL Query %s" % (self.query))

        gql_c = GraphQLClient("http://localhost:8080/v1/graphql")
        resp = gql_c.http_execute(query)
        if resp is not None:
            if resp.status_code < 300:
                if event_per_result:
                    j_obj = json.loads(resp.content)
                    s = 1
                    if "data" in j_obj:
                        for k, v in j_obj["data"].items():
                            for it in v:
                                yield {'_serial': s, '_time': time.time(), 'sourcetype': "_json", 'table': k ,'status_code': resp.status_code, '_raw': json.dumps(it)}    
                                s = s + 1
                    else:
                        yield {'_serial': 1, '_time': time.time(), 'sourcetype': "_json", 'status_code': resp.status_code, '_raw': resp.content}    
                else:
                    yield {'_serial': 1, '_time': time.time(), 'sourcetype': "_json", 'status_code': resp.status_code, '_raw': resp.content}
            else:
                raise Exception("HTTP Status: %i Content: %s" % (resp.status_code, resp.content))    
        else:
            raise Exception("GQL Query Failed.")    
        # for i in range(1, self.count + 1):
        #     yield {'_serial': i, '_time': time.time(), '_raw': six.text_type(i) + '. ' + text}

dispatch(GraphQLQuery, sys.argv, sys.stdin, sys.stdout, __name__)