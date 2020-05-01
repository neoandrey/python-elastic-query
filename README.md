# elastic-query
######  An Ansible module for running queries against Elasticsearch and filtering results arbitrarily

The elastic_query module seeks to extend the reach of ansible by allowing it query the Elasticsearch API for specific information and initiate subsequent tasks based on the results returned.
It was written in accordance with the standard structure of ansible modules descrided in the [Ansible documentation](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
Once you have Ansible installed, using this module is as easy as:
1. Cloning this repository - run the command  ```git clone https://github.com/neoandrey/python-elastic-query.git```
2. Navigating to the folder that contains the elastic_query.py script.
3. Copying elastic_query.py script to the Ansible module library e.g. run the command ```cp ./elastic_query.py /usr/share/ansible/plugins/modules```
4. Specifying elastic_query as the task module to be run and providing required parameters in a play or command e.g. 
```
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
```
It is important to note that this module runs locally on the Ansible server and not remotely on hosts specified in the ansible inventory. However, the result of module can be passed to others tasks a play.

## Parameters
1. **index_name_prefix**: This *string* parameter specifies the name of the index in elastic search that should be queried. It is defined as a prefix to cater for indexes that may change daily and require the current date to be suffixed to them in order to reference the latest index.
2. **full_date_format**: This *string* parameter  is used to specify the full date format to be used to compare the current date and time of the ansible server with the date\time field stored in Elastic search. The default value is '%Y-%m-%d %H:%M:%SZ'
3. **date_format**: This *string* parameter  is used to specify the date format to be used as a suffix to be appended to the value of the **index_name_prefix** parameter. It allows ansible identify and query the most recent Elastic index. It would only be used if the value of the **is_date_suffixed** parameter is set to True or 1 .Otherwise, it is ignored. The default value is '%Y-%m-%d %H:%M:%SZ'
4. **elastic_host**: This *string* parameter specifies the resolvable name of IP address of the Elasticsearch cluster. The elastic host should be accessible to the ansible server either directly or through the system or environment proxy. The default value is localh1ost.
5. **elastic_port**: This *integer* parameter specifies the port used to access the Elastic cluster. The default value  is 9200
6. **search_size**:  This *integer* parameter specifies the number of matching rows to be returned by the query module.	 The  default value is 1000 but can generally go up to 10,000.
7. **use_proxy**: This *boolean* parameter determines if a system or environment proxy should be used to access the  Elasticsearch cluster.  This parameter is False by default.
8. **past_minutes_to_check**: This *integer* parameter specifies how far back from the  current date and time on the Ansible server should a search filter records from the Elasticsearch cluster if the **is_time_dependent** parameter is set to True. Otherwise, it is ignored. The default value is  60.
9. **is_date_suffixed**: This *boolean* paramter determines if the **index_name_prefix** is suffixed with the current date in the format specified by the **date_format** parameter. The default value of this parameter is True.
10. **is_run_check**: This *boolean* parameter is used to run the module without filtering results in order to test if the ElasticSearch cluster is accessible from the  Ansible server. The default value of this parameter is False.
11. **search_query_map**: This *dictionary* or hashmap parameter specifies the fields of the Elastic index that should be filtered. The values of each of the fields specified would be used to filter the data and produce the desired results
12. **field_comparison_map**:  This *dictionary* or hashmap parameter is used to specify how each field in the **search_query_map** parameter should be compared with the fields in of the Elasticsearch index. Posible values are:
```
 - 'eq': a == b
 - 'ne': a!= b
 - 'gt': a > b
 - 'ge': a > b
 - 'le': a < b
 - 'like': a in b
 - 'notlike': a not in b
 ```
 13. **search_field_map**: This *dictionary* or hashmap parameter specifies fields of the Elasticsearch index that should be returned from the query and the keys each field should be returned as.From the [Elasticsearch docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html), fields may be nested and to cater for this, the dot(.) notation is used e.g. 'component': 'object.source.component'. 
 14. **is_time_dependent**: This *boolean* parameter is used to instruct the module to search as far back as specified by the *past_minutes_to_check* parameter. The default value is  True. 

The following section of the play above stores the output of the module in the *result* variable. It then iterates through the  
results (result.meta) and adds the trans_source property each item as a host in the 'filtered_server' group.Thie group can then be used in subsequent tasks e.q. restart apache http server on each filtered server
```
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
```
