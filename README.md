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
