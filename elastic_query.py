#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: elastic_query

short_description: Module for querying elastic search

version_added: "2.4"

description:
    - "This module queries elastic search based on parameters provided for search and returns results that may be used to perform further tasks"

options:
    name:
        description:
            - A simple test would query the provided elastic search instance and display the results
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - elasticsearch

author:
    - Bolaji Aina(neoandrey@gmail.com)
'''
EXAMPLES = '''
- hosts: localhost
  tasks:
   - name: test
     elastic_query:
       is_run_check: 0
       index_name_prefix: august_transactions
       full_date_format: '%Y-%m-%d %H:%M:%SZ'
       date_format: '%Y.%m.%d'
       elastic_host: 'localhost'
       elastic_port: 9200
       search_size: 1000
       use_proxy: 0
       past_minutes_to_check: 60
       is_date_suffixed: 0
       is_time_dependent: 0
       search_query_map:
        'request_date': '2018-08-02'
       field_comparison_map:
        'request_date': 'like'
       search_field_map:
        'request_date': 'request_date'
        'trans_source': 'trans_source'
        'tran_value': 'tran_value'
        'tran_value_received': 'tran_value_received'
        'amount_settled': 'amount_settled'
        'amount_settled_2': 'amount_settled_2'
        'terminal_holder': 'terminal_holder'
        'trans_message': 'trans_message'
        'tran_req_code': 'tran_req_code'
        'tran_rsp_code': 'tran_rsp_code'
     register: result
   - add_host:
      groups: filtered_servers
      hostname: "{{ item['trans_source'] }}"
     with_items: "{{ result.meta }}"
   - debug: var=groups.filtered_servers
- hosts: filterd_servers
  tasks:
   - name: Restart Apache HTTP on  filtered servers 
     service:
        name: httpd
        state: restarted
'''
#-*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import *

import traceback
import json #, requests
from datetime import datetime, date,timedelta
import time
import os
import os.path
os.path.dirname(__file__)

def filter_event_data(a,b, comparison):
    a = a.lower() 
    b = b.lower() 
    comparison = comparison.lower().strip()
    if  comparison == 'eq':
        return  a==b
    elif comparison == 'ne':
        return  a != b
    elif comparison == 'gt':
        return  a > b
    elif comparison == 'ge':
        return  a > b
    elif comparison == 'le':
        return  a < b
    elif comparison == 'like':
        return  a in b
    elif comparison == 'notlike':
        return  a not in b
    
def get_elastic_field(key,event_source):
    key_properties  = []
    key_properties = key.split('.')
    if len(key_properties)== 1:
        return event_source[key]
    else:
       temp   = event_source
       for sub_key in key_properties:
           temp = temp[sub_key]
       #print("key: k, value: {}".format(key,temp))
       return temp
        
def run_elastic_query(src_options):
        try: 
            full_date_format     = src_options['full_date_format']
            date_format          = src_options['date_format']
            elastic_host         = src_options['elastic_host']
            elastic_port         = src_options['elastic_port']
            index_name_prefix    = src_options['index_name_prefix']
            search_size          = src_options['search_size']
            use_proxy            = src_options['use_proxy']
            past_minutes_to_check= src_options['past_minutes_to_check']
            check_time           =  datetime.now() - timedelta(minutes=past_minutes_to_check) 
            index_name           = ""
            today_in_full        = datetime.now().strftime(full_date_format)
            today                = datetime.now().strftime(date_format)
            is_date_suffixed     = src_options['is_date_suffixed']
            search_query_map     = src_options['search_query_map']
            field_comparison_map = src_options['field_comparison_map']
            is_run_check         = src_options['is_run_check']
            search_field_map     = src_options['search_field_map']
            is_time_dependent    = src_options['is_time_dependent']
            if is_time_dependent:
                url_data = """{
                "query":{"match_all" : {}},
                "sort": { "date_field" : {"order" : "desc"}}
               }""".replace('date_field',search_field_map['time'])
            else:
              url_data="""{
                 "query" : {
                    "match_all" : {}
                 }
               }"""
            if len(field_comparison_map.items()) != len(search_query_map.items()):
               return  {'error':'Each field in search_query_map must have a corresponding field_comparison_map entry'}
            for k,v in  search_query_map.items():
                if field_comparison_map[k] is None:
                    return  {'error':'Each field in search_query_map must have a corresponding field_comparison_map entry'}                
            if is_date_suffixed:
                    index_name=index_name_prefix+today
            else:
                    index_name=index_name_prefix
            headers              = {'Content-type': 'application/json'}
            base_url             = "http://"+elastic_host+":"+str(elastic_port)+"/"+index_name+"/_search?size="
            url                  = base_url+str(search_size)
            f                    = open_url(url, headers=headers, data=url_data, use_proxy=use_proxy)
            result               = json.loads(f.read())
            elastic_data         = result['hits']['hits']
            event_filter         = {}
            json_response        = {}
            if is_time_dependent:
                event_filter["time"]    = check_time
            for k,v    in   search_query_map.items():
                event_filter[k]  = v
            if is_run_check != True:
                matching_records  =[]
                for event in  elastic_data:
                  try:
                    event                = event['_source']
                    record_event         =     {}
                    for key, value  in search_field_map.items():
                        record_event[key]  = get_elastic_field(value,event)
                    match_count = 0
                    for k, v in event_filter.items():
                        if k!="time" and filter_event_data(str(event_filter[k]),str(record_event[k]),field_comparison_map[k] ):
                           match_count=match_count+1
                        elif k.lower() == "time":
                            event_time     = datetime.strptime(record_event['time'].replace('T',' ').split('.')[0], full_date_format)
                            threshold_time = v
                            diff = event_time.replace(tzinfo=None)  - v.replace(tzinfo=None) 
                            if (not str(diff).startswith('-')) and diff.seconds >=0:
                               match_count= match_count+1
                    if match_count == len(event_filter):
                       matching_records.append(record_event)
                  except:
                    record_event         =     {}
                json_response = json.dumps(matching_records)
                return  json_response
            else:
                return result
        except:
           return  {'error':traceback.format_exc()}
def run_module():
    # define available arguments/parameters a user can pass to the module
    #module_args = dict(
    #    name=dict(type='str', required=True),
    #    new=dict(type='bool', required=False, default=False)
    #)
    module_args = dict(
	index_name_prefix      = dict(type='str',  default='kube-events-')
	,full_date_format      = dict(type='str',  default='%Y-%m-%d %H:%M:%SZ')
	,date_format           = dict(type='str',  default='%Y.%m.%d')
	,elastic_host 	       = dict(type='str',  default='172.38.1.126')
	,elastic_port          = dict(type='int',  default=9200)
	,search_size	       = dict(type='int',  default=1000)
	,use_proxy	       = dict(type='bool', default=False)
	,past_minutes_to_check = dict(type='int',  default=60)
	,is_date_suffixed      = dict(type='bool', default=True)
        ,is_run_check          = dict(type='bool', default=False)
	,search_query_map      = dict(type='dict', required=True)
        ,field_comparison_map  = dict(type='dict', required=True)
	,search_field_map      = dict(type='dict', required=True)
 	,is_time_dependent     = dict(type='bool', required=True)  
    )			
    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    #print('Running module with parameters:{} '.format(module_args))
    result = dict(
        changed		=False,
        original_message='',
        message		='',
        meta  		={},
        error     	={}
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.params['is_run_check'] = True
        result['meta']   = run_elastic_query(module.params)
        module.exit_json(**result)
    else:
      # manipulate or modify the state as needed (this is going to be the
      # part where your module will do what it needs to do)
      result['meta']      = json.loads(run_elastic_query(module.params))

    #result['original_message'] = module.params['name']
    #result['message']          = 'goodbye'

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if bool(result['error']):
        result['changed']          = False
        result['message']          = "No results found due to error: {}".format(result['error'])
        result['error']            = result['error']
        module.fail_json(**result)
    if len( result['meta']) >=0:
        result['changed']          = True
        result['message']          = "{} matching record(s) found".format(len( result['meta'] ))
        result['error']            = {}
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

