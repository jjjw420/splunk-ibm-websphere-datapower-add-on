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
import os
import sys
import requests
import json

splunkhome = os.environ['SPLUNK_HOME']
sys.path.append(os.path.join(splunkhome, 'etc', 'apps', 'searchcommands_app', 'lib'))
from splunklib.searchcommands import dispatch, StreamingCommand, Configuration, Option, validators

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
   



@Configuration()
class UpdateServiceRepoTableCommand(StreamingCommand):
    """ Update a particular table in the service repo.

    ##Syntax

    .. code-block::
        updaterepotable fields=<fields csv> where_fields=<where fields csv> table_name=<table_name>

    ##Description

    Update a Service Repo Table

    ##Example

    Update Host with Address
    .. code-block::
        | inputlookup tweets | countmatches fieldname=word_count pattern="\\w+" text

    """
    table_name = Option(
        doc='''
        **Syntax:** **table_name=***<table_name>*
        **Description:** The table to be updated.''',
        require=True, validate=validators.Fieldname())

    fields = Option(
        doc='''
        **Syntax:** **fields=***<fields>*
        **Description:** The fields to be updated.  Comma delimited.  USe Source:Target form if field names in the event do not match that of the table.''',
        require=True)

    where_fields = Option(
        doc='''
        **Syntax:** **where_fields=***<where_fields>*
        **Description:** The fields to match on in the where clause.  Comma delimited. Use Soure:Target  form if fields names in the event do not match that of the table.''',
        require=True)

    def stream(self, records):

        self.logger.debug('UpdateServiceRepoCommand: %s', self)  # logs command line

        gql_c = GraphQLClient("http://localhost:8080/v1/graphql")

        where_fields = self.where_fields
        table_name = self.table_name
        fields = self.fields

        sys.stderr.write("\nin stream!!")


        sys.stderr.write("\nbefore field_name_map!!")
        sys.stderr.write("\nfields: %s" % (fields))
        sys.stderr.write("\nwhere fields: %s" % (where_fields))
        field_name_map = {}
        field_name_lst = fields.split(",")
        field_vars = {}
        sys.stderr.write("\nfield_name_lst: %s" % (str(field_name_lst)))
        for i in field_name_lst:
            sys.stderr.write("\ni: %s" % (str(i)))
            if i.strip() == "":
                field_name_lst.remove(i)
                continue
            p = i.find(":")
            if p > 0:
                sys.stderr.write("\np gt 0: %s" % (str(p)))
                s = i[:p]
                t = i[p+1:]
                
                if len(s) == 0:
                    if len(t) == 0:
                        pass
                    else:
                        field_name_map[t] = t        
                else:
                    if len(t) == 0:
                        field_name_map[s] = s         
                    else:
                        field_name_map[s] = t
            else:
                field_name_map[i] = i

        sys.stderr.write("\nbefore where_field_name_map!!")
        where_field_name_map = {}
        where_field_name_lst = where_fields.split(",")
        sys.stderr.write("\nwhere_field_name_lst: %s" % (str(where_field_name_lst)))
        for i in where_field_name_lst:
            i = i.strip()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
            sys.stderr.write("\nw_i: %s" % (str(i)))
            if i == "":
                where_field_name_lst.remove(i)
                continue
            
            sys.stderr.write("\nbefore find")
            op = "_eq"
            if i.startswith("_"):
                p = i.find(":")
                if p > 0:
                    op = i[:p]
                    i = i[p+1:]

            p = i.find(":")
            sys.stderr.write("\nafter find")
            sys.stderr.write("\np: %s" % (str(p)))
            if p > 0:
                s = i[:p]
                sys.stderr.write("\ns: %s" % (str(s)))
                sys.stderr.write("\nw_i: %s" % (str(i)))
                t = i[p+1:]
                sys.stderr.write("\nt: %s" % (str(t)))
                if len(s) == 0:
                    if len(t) == 0:
                        pass
                    else:
                        where_field_name_map[t] = (op,t)        
                else:
                    if len(t) == 0:
                       where_field_name_map[s] = (op,s)         
                    else:
                        where_field_name_map[s] = (op,t)
            else:
                where_field_name_map[i] = (op,i)

        self.logger.debug('field_name_map: %s', str(field_name_map))  
        self.logger.debug('where_field_name_map: %s', str(where_field_name_map))  
        sys.stderr.write("\nfield_name_map: %s" % (str(field_name_map)))
        sys.stderr.write("\where_field_name_map: %s" % (str(where_field_name_map)))
        for record in records:
            mut_q = """
mutation MyMutation%s {
  update_servicerepo_%s(where: {%s}, _set: {%s}) {
    affected_rows
  }
}
"""
            v_str = ""
            w_str = ""
            for s_w, t_w in where_field_name_map.items():
                if s_w.startswith("$"):
                    t_p = s_w.find("!")
                    if t_p > 0:
                        t_t = s_w[t_p+1:]
                        s_w = s_w[:t_p]
                        v_str = v_str + "%s: %s," % (s_w, t_t)
                    else:
                        t_t = "String"
                        v_str = v_str + "%s: %s," % (s_w, t_t)

                    s_w = s_w.replace("$", "")
                    w_str = w_str + '%s: {%s: %s},' % (t_w[1], t_w[0], record[s_w])
                    field_vars[s_w] = json.loads(record[s_w])
                else:
                    if t_w[1].endswith("#") or s_w.endswith("#"):
                        w_str = w_str + '%s: {%s: %s},' % (t_w[1].replace("#", ""), t_w[0], record[s_w.replace("#", "")])
                    else:
                        w_str = w_str + '%s: {%s: "%s"},' % (t_w[1], t_w[0], record[s_w])    

            if len(w_str) > 0:
                w_str = w_str[:-1]

            s_str = ""
            for s_s, t_s in field_name_map.items():
                if s_s.startswith("$"):
                    t_p = s_s.find("!")
                    t_t = "String"
                    if t_p > 0:
                        t_t = s_s[t_p+1:]
                        s_s = s_s[:t_p]
                        v_str = v_str + "%s: %s," % (s_s, t_t)
                    else:
                        t_t = "String"
                        v_str = v_str + "%s: %s," % (s_s, t_t) 

                    s_str = s_str + '%s: %s,' % (t_s.replace("$", ""), s_s)
                    s_s = s_s.replace("$", "")
                    sys.stderr.write("\ns_s: %s!!\n" % (s_s))
                    if t_t != "Int" and t_t != "jsonb":
                        sys.stderr.write("\nt_t: %s!!\n" % (t_t))
                        if not (record[s_s].startswith('"') and record[s_s].endswith('"')):
                            record[s_s] = '"' + record[s_s] + '"'
                        field_vars[s_s] = json.loads(record[s_s])
                    else:
                        sys.stderr.write("\nt_t: %s!!\n" % (t_t))
                        field_vars[s_s] = json.loads(record[s_s])
                else:
                    if s_s.endswith("#") or t_s.endswith("#"):
                        sys.stderr.write("\ns_s: %s!!\n" % (s_s))
                        s_str = s_str + '%s: %s,' % (t_s.replace("#", ""), record[s_s.replace("#", "")])
                    else:                        
                        s_str = s_str + '%s: "%s",' % (t_s, record[s_s])

            if len(s_str) > 0:
                s_str = s_str[:-1]

            if len(v_str) > 0:
                v_str = "(" + v_str[:-1] + ")"

            new_mut_q = mut_q % (v_str, table_name, w_str, s_str)
            sys.stderr.write("\nnew_mut_q: %s!!\n" % (new_mut_q))
            sys.stderr.write("\nfield_vars: %s!!\n" % (field_vars))
            gql_r = gql_c.http_execute(new_mut_q, field_vars)
            if gql_r is not None:
                if gql_r.status_code < 300:
                    record["update_status"] = "Update Ok(%d). Output: %s" % (gql_r.status_code, gql_r.content)
                else:
                    record["update_status"] = "Update Failed(%d). Output: %s" % (gql_r.status_code, gql_r.content)
            else:
                record["update_status"] = "Failed Unexpected. No object was returned."

            sys.stderr.write("\gql_r: %s!!\n" % (str(gql_r)))
            #record[self.fieldname] = count
            yield record

dispatch(UpdateServiceRepoTableCommand, sys.argv, sys.stdin, sys.stdout, __name__)