'''
IBM Websphere Datapower Modular Input for Splunk
Hannes Wagener - 2016

Datapower statistcs input. 
Statistics and their intervals can be selected.


DISCLAIMER
You are free to use this code in any way you like, subject to the
Python & IBM disclaimers & copyrights. I make no representations
about the suitability of this software for any purpose. It is
provided "AS-IS" without warranty of any kind, either express or
implied.

'''
from __future__ import print_function

import requests
import sys
import logging
import time
import threading
import uuid
import cgi
import datetime
import json
import collections
import splunklib.client 
import splunklib.results
import splunklib.modularinput

# Initialize the root logger with a StreamHandler and a format message:
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class DPStatsInput(splunklib.modularinput.Script):

    def get_scheme(self):
        # Returns scheme.
        scheme = splunklib.modularinput.Scheme("IBM Websphere Datapower Statistics")
        scheme.description = "IBM Websphere Datapower Statistics Input for Splunk."
        scheme.use_external_validation = True
        scheme.use_single_instance = False

        device_name_argument = splunklib.modularinput.Argument("device_name")
        device_name_argument.data_type = splunklib.modularinput.Argument.data_type_string
        device_name_argument.title = "Device Name"
        device_name_argument.description = "Name of the Datapower device to monitor."
        device_name_argument.required_on_create = True
        device_name_argument.required_on_edit = False
        scheme.add_argument(device_name_argument)

        device_host_argument = splunklib.modularinput.Argument("device_host")
        device_host_argument.data_type = splunklib.modularinput.Argument.data_type_string
        device_host_argument.title = "Datapower Device Hostname or IP"
        device_host_argument.description = "IP or hostname of the Datapower device to be monitored."
        device_host_argument.required_on_create = True
        device_host_argument.required_on_edit = False
        scheme.add_argument(device_host_argument)

        rest_port_argument = splunklib.modularinput.Argument("rest_port")
        rest_port_argument.data_type = splunklib.modularinput.Argument.data_type_number
        rest_port_argument.title = "REST Port"
        rest_port_argument.description = "The REST Management interface port number."
        rest_port_argument.required_on_create = False
        rest_port_argument.required_on_edit = False
        scheme.add_argument(rest_port_argument)

        rest_user_argument = splunklib.modularinput.Argument("rest_user")
        rest_user_argument.data_type = splunklib.modularinput.Argument.data_type_string
        rest_user_argument.title = "REST user"
        rest_user_argument.description = "The user to use when using the REST Management Interface."
        rest_user_argument.required_on_create = True
        rest_user_argument.required_on_edit = False
        scheme.add_argument(rest_user_argument)

        rest_user_password_argument = splunklib.modularinput.Argument("rest_user_password")
        rest_user_password_argument.data_type = splunklib.modularinput.Argument.data_type_string
        rest_user_password_argument.title = "REST user password"
        rest_user_password_argument.description = "The REST user's password."
        rest_user_password_argument.required_on_create = True
        rest_user_password_argument.required_on_edit = False
        scheme.add_argument(rest_user_password_argument)
                
        dpinput_interval_argument = splunklib.modularinput.Argument("dpinput_interval")
        dpinput_interval_argument.data_type = splunklib.modularinput.Argument.data_type_number
        dpinput_interval_argument.title = "Input check interval"
        dpinput_interval_argument.description = "How often to run the MQ input script. Defaults to 60 seconds."
        dpinput_interval_argument.required_on_create = False
        dpinput_interval_argument.required_on_edit = False
        scheme.add_argument(dpinput_interval_argument)

        cpu_usage_int_argument = splunklib.modularinput.Argument("cpu_usage_int")
        cpu_usage_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        cpu_usage_int_argument.title = "CPU Usage Interval"
        cpu_usage_int_argument.description = "How often to capture CPU usage statistics. Defaults to 60 seconds."
        cpu_usage_int_argument.required_on_create = False
        cpu_usage_int_argument.required_on_edit = False
        scheme.add_argument(cpu_usage_int_argument)
            
        conns_accepted_int_argument = splunklib.modularinput.Argument("conns_accepted_int")
        conns_accepted_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        conns_accepted_int_argument.title = "Connections Accepted Interval"
        conns_accepted_int_argument.description = "How often to capture Connection Accepted statistics. Defaults to 60 seconds."
        conns_accepted_int_argument.required_on_create = False
        conns_accepted_int_argument.required_on_edit = False
        scheme.add_argument(conns_accepted_int_argument)
            
        memory_int_argument = splunklib.modularinput.Argument("memory_int")
        memory_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        memory_int_argument.title = "Memory Usage Interval"
        memory_int_argument.description = "How often to capture Memory usage statistics. Defaults to 300 seconds."
        memory_int_argument.required_on_create = False
        memory_int_argument.required_on_edit = False
        scheme.add_argument(memory_int_argument)
            
        file_system_int_argument = splunklib.modularinput.Argument("file_system_int")
        file_system_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        file_system_int_argument.title = "Filesystem Status Interval"
        file_system_int_argument.description = "How often to capture filesystem statistics. Defaults to 300 seconds."
        file_system_int_argument.required_on_create = False
        file_system_int_argument.required_on_edit = False
        scheme.add_argument(file_system_int_argument)

        tx_rx_kbps_thruput_int_argument = splunklib.modularinput.Argument("tx_rx_kbps_thruput_int")
        tx_rx_kbps_thruput_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        tx_rx_kbps_thruput_int_argument.title = "Network Transmit and Receive Kbps Interval"
        tx_rx_kbps_thruput_int_argument.description = "How often to capture Network Transmit and Receive Kbps statistics. Defaults to 60 seconds."
        tx_rx_kbps_thruput_int_argument.required_on_create = False
        tx_rx_kbps_thruput_int_argument.required_on_edit = False
        scheme.add_argument(tx_rx_kbps_thruput_int_argument)
            
        network_int_argument = splunklib.modularinput.Argument("network_int")
        network_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        network_int_argument.title = "Network Statistics Interval"
        network_int_argument.description = "How often to capture Network and TCP related statistics. Defaults to 300 seconds."
        network_int_argument.required_on_create = False
        network_int_argument.required_on_edit = False
        scheme.add_argument(network_int_argument)
            
        system_usage_int_argument = splunklib.modularinput.Argument("system_usage_int")
        system_usage_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        system_usage_int_argument.title = "System Usage Interval"
        system_usage_int_argument.description = "How often to capture System usage statistics. Defaults to 300 seconds."
        system_usage_int_argument.required_on_create = False
        system_usage_int_argument.required_on_edit = False
        scheme.add_argument(system_usage_int_argument)


        enable_stats_argument = splunklib.modularinput.Argument("enable_stats")
        enable_stats_argument.data_type = splunklib.modularinput.Argument.data_type_number
        enable_stats_argument.title = "Enable statistics on the device. "
        enable_stats_argument.description = "Enable statistics on the device. NOTE: This affects a change on the device."
        enable_stats_argument.required_on_create = False
        enable_stats_argument.required_on_edit = False
        scheme.add_argument(enable_stats_argument)

        enable_stats_domains_argument = splunklib.modularinput.Argument("enable_stats_domains")
        enable_stats_domains_argument.data_type = splunklib.modularinput.Argument.data_type_string
        enable_stats_domains_argument.title = "Enable statistics on the listed domains.  Comma delimited. "
        enable_stats_domains_argument.description = "Enable statistics on the listed domains.  Comma delimited.  If ommitted statistics are enabled in all domains."
        enable_stats_domains_argument.required_on_create = False
        enable_stats_domains_argument.required_on_edit = False
        scheme.add_argument(enable_stats_domains_argument)

 
        only_eth_ints_with_ips_argument = splunklib.modularinput.Argument("only_eth_ints_with_ips")
        only_eth_ints_with_ips_argument.data_type = splunklib.modularinput.Argument.data_type_number
        only_eth_ints_with_ips_argument.title = "Ethernet Interfaces with IP's only."
        only_eth_ints_with_ips_argument.description = "Capture network statistics for interfaces with IP's only."
        only_eth_ints_with_ips_argument.required_on_create = False
        only_eth_ints_with_ips_argument.required_on_edit = False
        scheme.add_argument(only_eth_ints_with_ips_argument)
               
        active_users_argument = splunklib.modularinput.Argument("active_users")
        active_users_argument.data_type = splunklib.modularinput.Argument.data_type_number
        active_users_argument.title = "Capture Active User Status"
        active_users_argument.description = "Capture Active User Status. "
        active_users_argument.required_on_create = False
        active_users_argument.required_on_edit = False
        scheme.add_argument(active_users_argument)
            
        active_users_int_argument = splunklib.modularinput.Argument("active_users_int")
        active_users_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        active_users_int_argument.title = "Capture Active User Status Interval"
        active_users_int_argument.description = "How often to capture active user status output. Defaults to 900 seconds."
        active_users_int_argument.required_on_create = False
        active_users_int_argument.required_on_edit = False
        scheme.add_argument(active_users_int_argument)
            
        date_time_status_argument = splunklib.modularinput.Argument("date_time_status")
        date_time_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        date_time_status_argument.title = "Capture Date and time Status"
        date_time_status_argument.description = "Capture Active Date and time Status. "
        date_time_status_argument.required_on_create = False
        date_time_status_argument.required_on_edit = False
        scheme.add_argument(date_time_status_argument)
            
        date_time_status_int_argument = splunklib.modularinput.Argument("date_time_status_int")
        date_time_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        date_time_status_int_argument.title = "Capture Date and time Status Interval"
        date_time_status_int_argument.description = "How often to capture date and time status output. Defaults to 900 seconds."
        date_time_status_int_argument.required_on_create = False
        date_time_status_int_argument.required_on_edit = False
        scheme.add_argument(date_time_status_int_argument)
            
        domain_status_argument = splunklib.modularinput.Argument("domain_status")
        domain_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        domain_status_argument.title = "Capture Domain Status"
        domain_status_argument.description = "Capture Domain Status. "
        domain_status_argument.required_on_create = False
        domain_status_argument.required_on_edit = False
        scheme.add_argument(domain_status_argument)
            
        domain_status_int_argument = splunklib.modularinput.Argument("domain_status_int")
        domain_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        domain_status_int_argument.title = "Capture Domain Status Interval"
        domain_status_int_argument.description = "How often to capture domain status output. Defaults to 900 seconds."
        domain_status_int_argument.required_on_create = False
        domain_status_int_argument.required_on_edit = False
        scheme.add_argument(domain_status_int_argument)
            
        log_target_status_argument = splunklib.modularinput.Argument("log_target_status")
        log_target_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        log_target_status_argument.title = "Capture Log Target Status"
        log_target_status_argument.description = "Capture Log Target Status. "
        log_target_status_argument.required_on_create = False
        log_target_status_argument.required_on_edit = False
        scheme.add_argument(log_target_status_argument)
            
        log_target_status_int_argument = splunklib.modularinput.Argument("log_target_status_int")
        log_target_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        log_target_status_int_argument.title = "Capture Log Target Status Interval"
        log_target_status_int_argument.description = "How often to capture log target status output. Defaults to 900 seconds."
        log_target_status_int_argument.required_on_create = False
        log_target_status_int_argument.required_on_edit = False
        scheme.add_argument(log_target_status_int_argument)
            
        object_status_argument = splunklib.modularinput.Argument("object_status")
        object_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        object_status_argument.title = "Capture Object Status"
        object_status_argument.description = "Capture Object Status. "
        object_status_argument.required_on_create = False
        object_status_argument.required_on_edit = False
        scheme.add_argument(object_status_argument)
            
        object_status_int_argument = splunklib.modularinput.Argument("object_status_int")
        object_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        object_status_int_argument.title = "Capture Object Status Interval"
        object_status_int_argument.description = "How often to capture object status output. Defaults to 900 seconds."
        object_status_int_argument.required_on_create = False
        object_status_int_argument.required_on_edit = False
        scheme.add_argument(object_status_int_argument)
            
        http_status_argument = splunklib.modularinput.Argument("http_status")
        http_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        http_status_argument.title = "Capture HTTP statistics"
        http_status_argument.description = "Capture HTTP related statistics. Will capture statistics for all domains."
        http_status_argument.required_on_create = False
        http_status_argument.required_on_edit = False
        scheme.add_argument(http_status_argument)
            
        http_int_argument = splunklib.modularinput.Argument("http_int")
        http_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        http_int_argument.title = "HTTP statistics interval"
        http_int_argument.description = "How often to capture HTTP related statistics. Defaults to 60."
        http_int_argument.required_on_create = False
        http_int_argument.required_on_edit = False
        scheme.add_argument(http_int_argument)
            
        service_memory_status_argument = splunklib.modularinput.Argument("service_memory_status")
        service_memory_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        service_memory_status_argument.title = "Capture Service Memory statistics"
        service_memory_status_argument.description = "Capture Service memory statistics. Will capture statistics for all domains."
        service_memory_status_argument.required_on_create = False
        service_memory_status_argument.required_on_edit = False
        scheme.add_argument(service_memory_status_argument)
            
        load_balancer_status_argument = splunklib.modularinput.Argument("load_balancer_status")
        load_balancer_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        load_balancer_status_argument.title = "Capture Load Balancer Status"
        load_balancer_status_argument.description = "Capture Load Balancer Status. "
        load_balancer_status_argument.required_on_create = False
        load_balancer_status_argument.required_on_edit = False
        scheme.add_argument(load_balancer_status_argument)
            
        load_balancer_status_int_argument = splunklib.modularinput.Argument("load_balancer_status_int")
        load_balancer_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        load_balancer_status_int_argument.title = "Capture Log Target Status Interval"
        load_balancer_status_int_argument.description = "How often to capture load balancer staus output. Defaults to 900 seconds."
        load_balancer_status_int_argument.required_on_create = False
        load_balancer_status_int_argument.required_on_edit = False
        scheme.add_argument(load_balancer_status_int_argument)
            
        sql_status_argument = splunklib.modularinput.Argument("sql_status")
        sql_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        sql_status_argument.title = "Capture SQL statistics."
        sql_status_argument.description = "Capture SQL related statistics. Will capture statistics for all domains."
        sql_status_argument.required_on_create = False
        sql_status_argument.required_on_edit = False
        scheme.add_argument(sql_status_argument)
            
        sql_int_argument = splunklib.modularinput.Argument("sql_int")
        sql_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        sql_int_argument.title = "SQL statistics interval"
        sql_int_argument.description = "How often to capture SQL related statistics. Defaults to 300."
        sql_int_argument.required_on_create = False
        sql_int_argument.required_on_edit = False
        scheme.add_argument(sql_int_argument)
            
        mq_status_argument = splunklib.modularinput.Argument("mq_status")
        mq_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        mq_status_argument.title = "Capture Websphere MQ statistics."
        mq_status_argument.description = "Capture Websphere MQ related statistics. Will capture statistics for all domains."
        mq_status_argument.required_on_create = False
        mq_status_argument.required_on_edit = False
        scheme.add_argument(mq_status_argument)
            
        mq_int_argument = splunklib.modularinput.Argument("mq_int")
        mq_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        mq_int_argument.title = "MQ statistics interval"
        mq_int_argument.description = "How often to capture MQ related statistics. Defaults to 300."
        mq_int_argument.required_on_create = False
        mq_int_argument.required_on_edit = False
        scheme.add_argument(mq_int_argument)
            
        sensors_status_argument = splunklib.modularinput.Argument("sensors_status")
        sensors_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        sensors_status_argument.title = "Capture Hardware and sensor statistics"
        sensors_status_argument.description = "Capture Hardware and other sensor statistics. "
        sensors_status_argument.required_on_create = False
        sensors_status_argument.required_on_edit = False
        scheme.add_argument(sensors_status_argument)
            
        sensors_int_argument = splunklib.modularinput.Argument("sensors_int")
        sensors_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        sensors_int_argument.title = "Hardware and Sensor statistics interval"
        sensors_int_argument.description = "How often to capture Hardware and Sensor related statistics. Defaults to 300."
        sensors_int_argument.required_on_create = False
        sensors_int_argument.required_on_edit = False
        scheme.add_argument(sensors_int_argument)
            
        xslt_status_argument = splunklib.modularinput.Argument("xslt_status")
        xslt_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        xslt_status_argument.title = "Capture XSLT statistics"
        xslt_status_argument.description = "Capture XSLT related statistics. Will capture statistics for all domains."
        xslt_status_argument.required_on_create = False
        xslt_status_argument.required_on_edit = False
        scheme.add_argument(xslt_status_argument)
            
        xslt_int_argument = splunklib.modularinput.Argument("xslt_int")
        xslt_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        xslt_int_argument.title = "XSLT and XML statistics interval"
        xslt_int_argument.description = "How often to capture XSLT and XML related statistics. Defaults to 300."
        xslt_int_argument.required_on_create = False
        xslt_int_argument.required_on_edit = False
        scheme.add_argument(xslt_int_argument)
            
        ws_op_status_argument = splunklib.modularinput.Argument("ws_op_status")
        ws_op_status_argument.data_type = splunklib.modularinput.Argument.data_type_number
        ws_op_status_argument.title = "Capture Web service operation metrics."
        ws_op_status_argument.description = "Capture Web service operation metrics. Will capture statistics for all domains."
        ws_op_status_argument.required_on_create = False
        ws_op_status_argument.required_on_edit = False
        scheme.add_argument(ws_op_status_argument)
            
        ws_op_status_int_argument = splunklib.modularinput.Argument("ws_op_status_int")
        ws_op_status_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        ws_op_status_int_argument.title = "Web servce operation statistics interval"
        ws_op_status_int_argument.description = "How often to capture web service operation related statistics. Defaults to 300."
        ws_op_status_int_argument.required_on_create = False
        ws_op_status_int_argument.required_on_edit = False
        scheme.add_argument(ws_op_status_int_argument)
            
        web_app_fw_stats_argument = splunklib.modularinput.Argument("web_app_fw_stats")
        web_app_fw_stats_argument.data_type = splunklib.modularinput.Argument.data_type_number
        web_app_fw_stats_argument.title = "Capture WebAppFw accepted and rejected statistics."
        web_app_fw_stats_argument.description = "Capture WebAppFw accepted and rejected statistics.. Will capture statistics for all domains."
        web_app_fw_stats_argument.required_on_create = False
        web_app_fw_stats_argument.required_on_edit = False
        scheme.add_argument(web_app_fw_stats_argument)
            
        web_app_fw_int_argument = splunklib.modularinput.Argument("web_app_fw_int")
        web_app_fw_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        web_app_fw_int_argument.title = "WebAppFw statistics interval"
        web_app_fw_int_argument.description = "How often to capture WebAppFw related statistics. Defaults to 300."
        web_app_fw_int_argument.required_on_create = False
        web_app_fw_int_argument.required_on_edit = False
        scheme.add_argument(web_app_fw_int_argument)
            
        wsm_stats_argument = splunklib.modularinput.Argument("wsm_stats")
        wsm_stats_argument.data_type = splunklib.modularinput.Argument.data_type_number
        wsm_stats_argument.title = "Capture WSM Agent and spoolers statistics"
        wsm_stats_argument.description = "Capture WSM Agent and spoolers related statistics. "
        wsm_stats_argument.required_on_create = False
        wsm_stats_argument.required_on_edit = False
        scheme.add_argument(wsm_stats_argument)
            
        wsm_stats_int_argument = splunklib.modularinput.Argument("wsm_stats_int")
        wsm_stats_int_argument.data_type = splunklib.modularinput.Argument.data_type_number
        wsm_stats_int_argument.title = "WSM Agent and spoolers statistics interval"
        wsm_stats_int_argument.description = "How often to capture WSM Agent and spoolers related statistics. Defaults to 300."
        wsm_stats_int_argument.required_on_create = False
        wsm_stats_int_argument.required_on_edit = False
        scheme.add_argument(wsm_stats_int_argument)

        return scheme

    def validate_input(self, validation_definition):
        # Validates input.

        rest_port = int(validation_definition.parameters["rest_port"])
        if rest_port <= 0 or rest_port > 65535:
            raise ValueError("REST port must be set to a valid port number between 0 and 65535. Port number:%d." % rest_port)

        device_host = validation_definition.parameters["device_host"]
        if device_host is None:
            raise ValueError("Device host is mandatory.")
        
        rest_user = validation_definition.parameters["rest_user"]
        if rest_user is None:
            raise ValueError("REST User name is mandatory.")
        
        rest_user_password = validation_definition.parameters["rest_user_password"]
        if rest_user_password is None:
            raise ValueError("REST User password is mandatory.")
        
        logging.debug("before val:" + str(validation_definition.parameters))
        if "dpinput_interval" in validation_definition.parameters:
            dpinput_interval = int(validation_definition.parameters["dpinput_interval"])
            if not dpinput_interval is None and int(dpinput_interval) < 1:
                raise ValueError("Script polling interval must be a positive integer")
#############################################################################################

    def get_domains(self, rest_session, device_host, rest_port, rest_user, rest_user_password):
        # domain_status = {"domain": "default", "status_class": "DomainStatus"}
        # domain_status_req = get_status_req.format(**domain_status)

        logging.debug("Getting domains from " + device_host)

        domain_list = None

        try:
            domain_status_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port, mgmt_uri="/mgmt/status/default/DomainStatus")
            r = rest_session.get(domain_status_url)

            if r.status_code != 200:
                logging.error("Get of domains for %s failed.  Status code: %i." % (device_host, r.status_code))
                return None
            else:
                logging.debug("Get of domains for %s OK!.  Status code: %i." % (device_host, r.status_code))
        
            #doc = lxml.etree.fromstring(r.content)

            domain_status_resp = json.loads(r.content)

            if "DomainStatus" not in domain_status_resp:
                logging.error("Get of domains for %s failed.  Status code: %i. Content: %s" % (device_host, r.status_code, r.content))
                return None
            logging.debug("domain_status_resp:" + str(domain_status_resp))
            domain_list = []
            if isinstance(domain_status_resp["DomainStatus"], list):
                for domain_status in domain_status_resp["DomainStatus"]:
                    if "Domain" in domain_status:
                        if domain_status["Domain"] not in domain_list:
                            domain_list.append(domain_status["Domain"])
            elif isinstance(domain_status_resp["DomainStatus"], dict):
                domain_status = domain_status_resp["DomainStatus"]
                if "Domain" in domain_status:
                    if domain_status["Domain"] not in domain_list:
                        domain_list.append(domain_status["Domain"])
                
        except Exception as ex:
            logging.error("Exception occurred while getting domains. Exception: " + str(ex))
 
        return domain_list

    def get_ws_operations_status(self, rest_session, device_host, domain, rest_port, rest_user, rest_user_password):
        # wsop_status = {"domain": domain, "status_class": "WSOperationsStatus"}
        # wsop_status_req = get_status_req.format(**wsop_status)

        logging.debug("Getting WSOP Status for " + device_host + " and domain " + domain)

        ws_op_dict = {}
        try:
            get_ws_op_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port, mgmt_uri="/mgmt/status/{domain}/WSOperationsStatusSimpleIndex".format(domain=domain))
            r = rest_session.get(get_ws_op_url)

            if r.status_code != 200:
                logging.error("Get of WS operation status failed for device %s and domain %s failed.  Status code: %i." % (device_host, domain,  r.status_code))
                return None
            else:
                pass
                #logging.debug("Get of WS operation status for device %s and domain %s OK!.  Status code: %i." % (device_host, domain, r.status_code))

            ws_op_status_resp = json.loads(r.content)
            logging.debug("ws_op_status_resp:" + str(ws_op_status_resp))
            if "WSOperationsStatusSimpleIndex" in ws_op_status_resp:
                for gw in ws_op_status_resp["WSOperationsStatusSimpleIndex"]:
                    port_n = None
                    url_n = None
                    wsg_n = None

                    if "Port" in gw:    
                        port_n = gw["Port"]
                    if "URL" in gw:
                        url_n = gw["URL"]
                    if "WSGateway" in gw:
                        if "value" in gw["WSGateway"]:
                            wsg_n = gw["WSGateway"]["value"]

                    if port_n is not None and url_n is not None and wsg_n is not None:
                        ws_op_dict[(port_n.text.strip(), url_n.text.strip())] = wsg_n.text
                    else:
                        logging.debug("WSOp status no Port, url or wsgateway found???")
            else:
                logging.debug("No WSOperationsStatusSimpleIndex resultS??")


        except Exception as ex:
            logging.error("Exception occurred while getting WSOP status. Exception: " + str(ex))

        return ws_op_dict

    def get_eth_ints_with_ips(self, rest_session, device_host, domain, rest_port, rest_user, rest_user_password):
        # ip_status = {"domain": domain, "status_class": "IPAddressStatus"}
        # ip_status_req = get_status_req.format(**ip_status)

        logging.debug("Getting IPAddressStatus Status for " + device_host + " and domain " + domain)

        network_stats_interface_list = None
        try:
            ip_status_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port,mgmt_uri="/mgmt/status/default/IPAddressStatus")
            r = rest_session.get(ip_status_url)

            if r.status_code != 200:
                logging.error("Get ofIPAddressStatus failed for device %s and domain %s failed.  Status code: %i." % (device_host, domain,  r.status_code))
                return None
            else:
                logging.debug("Get of IPAddressStatus for device %s and domain %s OK!.  Status code: %i." % (device_host, domain, r.status_code))

            ip_status_resp = json.loads(r.content)
            if "IPAddressStatus" in ip_status_resp:
                network_stats_interface_list = []
                for ip_s in ip_status_resp["IPAddressStatus"]:
                    if "Name" in ip_s:  
                        if ip_s["Name"] not in network_stats_interface_list:
                            network_stats_interface_list.append(ip_s["Name"])
                    else:
                        logging.error("Huh?? No Interface Name?")
            else:
                logging.error("No IPAddressStatus results?")

        except Exception as ex:
            logging.error("Exception occurred while getting domains. Exception: " + str(ex))

        return network_stats_interface_list

    def save_config(self, rest_session, device_host, rest_port, rest_user, rest_user_password, domain="default"):
        #domain_save_config_req = save_config_req.format(domain=domain)
        save_config_req = {
            "SaveConfig": {}
        }

        domain_save_config_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port, mgmt_uri="/mgmt/actionqueue/{domain}".format(domain=domain))

        try:
            #r = rest_session.post(self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port), data=domain_save_config_req, auth=(rest_user, rest_user_password), verify=False)
            r = rest_session.post(domain_save_config_url, json=save_config_req)

            if r.status_code != 200:
                logging.error("Request to save config for domain %s failed.  Status code: %i." % (domain, r.status_code))
                return False
            else:
                logging.debug("Request to save config for domain %s Ok.  Status code: %i." % (domain, r.status_code))
                return True
        
        except Exception as ex:
            logging.error("Exception occured while saving config for host %s and domain %s.  Exception: %s" % (device_host, domain, str(ex)))
            return False

    def get_config_enabled(self, rest_session, device_host, rest_port, rest_user, rest_user_password, domain, config_class):

        try:

            #rest_get_config_req = get_config_req.format(domain=domain, config_class=config_class)
            get_conf_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port, mgmt_uri="/mgmt/config/{domain}/{config_class}".format(domain=domain, config_class=config_class))
            #r = rest_session.post(self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port), data=domain_enable_stats_req, auth=(rest_user, rest_user_password), verify=False)
            r = rest_session.get(get_conf_url)

            if r.status_code != 200:
                logging.error("Request to get %s for domain %s failed.  Status code: %i." % (config_class, domain, r.status_code))
                return None
            else:
                logging.debug("Request to get %s for domain %s Ok.  Status code: %i." % (config_class, domain, r.status_code))
                #pass

            get_conf_resp = json.loads(r.content)
            if config_class in get_conf_resp:
                if "mAdminState" in get_conf_resp[config_class]:
                    if get_conf_resp[config_class]["mAdminState"] == "enabled":
                        logging.debug("admin state enabled? %s" % (get_conf_resp[config_class]["mAdminState"]))    
                        return True
                    else:
                        logging.debug("admin state disabled? %s" % (get_conf_resp[config_class]["mAdminState"]))    
                    return False
                else:
                    logging.error("Could not find mAdminState ??  Content: %s" % (r.content))    
                    return False
            else:
                logging.error("Could not find %s ??  Content: %s" % (config_class, r.content))
                return False        

        except Exception as ex:
            logging.error("Exception occurred while getting %s for host %s and domain %s.  Exception: %s" % (config_class, device_host, domain, str(ex)))
            return False

    def enable_statistics_domain(self, rest_session, device_host, rest_port, rest_user, rest_user_password, domain):
        
        enable_statistics_req = {
            "Statistics":    {
                "name": "default",
                "mAdminState": "enabled" 
            }   
        }

        try:
            #domain_enable_stats_req = enable_statistics_req.format(domain=domain)
            enable_stats_url = self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port, mgmt_uri="/mgmt/config/{domain}/Statistics/default".format(domain=domain))
            #r = rest_session.post(self.rest_mgmt_url.format(device_host=device_host, rest_port=rest_port), data=domain_enable_stats_req, auth=(rest_user, rest_user_password), verify=False)
            r = rest_session.put(enable_stats_url,json=enable_statistics_req)

            if r.status_code != 200:
                logging.error("Request to enable of stats for domain %s failed.  Status code: %i." % (domain, r.status_code))
                return None
            else:
                logging.debug("Request to enable of stats for domain %s Ok.  Status code: %i." % (domain, r.status_code))
                #pass

            return self.save_config(rest_session, device_host, rest_port, rest_user, rest_user_password, domain)

        except Exception as ex:
            logging.error("Exception occurred while enableling statistics for host %s and domain %s.  Exception: %s" % (device_host, domain, str(ex)))
            return False

    class RESTPollerThread(threading.Thread):

        def __init__(self, thread_id, input_name, input_item, ew, domain_wsm_op_dict, domain_list, network_stats_interface_list, **kw):

            threading.Thread.__init__(self)

            logging.debug("In _init__ for REST Polling Thread %s for input %s." % (thread_id, input_name))

            self.setName(thread_id)
            self.thread_id = thread_id
            self.input_name = input_name
            self.splunk_host = input_item["host"]
            self.device_name = input_item["device_name"]
            self.device_host = input_item["device_host"]
            self.rest_port = int(input_item["rest_port"])
            self.rest_user = input_item["rest_user"]
            self.rest_user_password = input_item["rest_user_password"]
            self.dpinput_interval = float(input_item["dpinput_interval"])
            self.cpu_usage_int = float(input_item["cpu_usage_int"])
            self.conns_accepted_int = float(input_item["conns_accepted_int"])
            self.memory_int = float(input_item["memory_int"])
            self.file_system_int = float(input_item["file_system_int"])
            self.tx_rx_kbps_thruput_int = float(input_item["tx_rx_kbps_thruput_int"])
            self.network_int = float(input_item["network_int"])
            self.system_usage_int = float(input_item["system_usage_int"])
            self.enable_stats = int(input_item["enable_stats"])
            self.enable_stats_domains = input_item["enable_stats_domains"]
            self.only_eth_ints_with_ips = int(input_item["only_eth_ints_with_ips"])

            self.active_users = int(input_item["active_users"])
            self.active_users_int = float(input_item["active_users_int"])
            self.date_time_status = int(input_item["date_time_status"])
            self.date_time_status_int = float(input_item["date_time_status_int"])

            self.domain_status = int(input_item["domain_status"])
            self.domain_status_int = float(input_item["domain_status_int"])

            self.log_target_status = int(input_item["log_target_status"])
            self.log_target_status_int = float(input_item["log_target_status_int"])

            self.object_status = int(input_item["object_status"])
            self.object_status_int = float(input_item["object_status_int"])

            self.http_status = int(input_item["http_status"])
            self.http_int = float(input_item["http_int"])

            self.service_memory_status = int(input_item["service_memory_status"])

            self.load_balancer_status = int(input_item["load_balancer_status"])
            self.load_balancer_status_int = float(input_item["load_balancer_status_int"])

            self.sql_status = int(input_item["sql_status"])
            self.sql_int = float(input_item["sql_int"])
            
            self.mq_status = int(input_item["mq_status"])
            self.mq_int = float(input_item["mq_int"])
            self.sensors_status = int(input_item["sensors_status"])
            self.sensors_int = float(input_item["sensors_int"])

            self.xslt_status = int(input_item["xslt_status"])
            self.xslt_int = float(input_item["xslt_int"])

            self.ws_op_status = int(input_item["ws_op_status"])
            self.ws_op_int = float(input_item["ws_op_status_int"])

            self.web_app_fw_stats = int(input_item["web_app_fw_stats"])
            self.web_app_fw_int = float(input_item["web_app_fw_int"])

            self.wsm_stats = int(input_item["wsm_stats"])
            self.wsm_stats_int = float(input_item["wsm_stats_int"])
            self.ew = ew
            #self.ws_op_dict = ws_op_dict
            self.domain_list = domain_list
            self.domain_wsm_op_dict = domain_wsm_op_dict
            self.network_stats_interface_list = network_stats_interface_list
            self.kw = kw

            self.rest_mgmt_url = "https://{device_host}:{rest_port}{mgmt_uri}"
            self.check_interval_dict = {}

        def log_event(self, ev_obj, event_time=None):

            if event_time is None:
                event_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z")
            ev_obj["time"] = event_time
            splunk_event = json.dumps(ev_obj)
            logging.debug("about to call ew.write_event")
            logging.error("event text:" + splunk_event)
            event = splunklib.modularinput.Event()
            event.stanza = self.input_name
            event.data = splunk_event
            
            self.ew.write_event(event)
            #self.print_xml_single_instance_mode(self.device_name, splunk_event)

        # def print_xml_single_instance_mode(self, host, event):
        #     #logging.debug("Logging event data: %s" % ("<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)))
        #     print("<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host))

        def run(self):
            logging.debug("RESTPollerThread run() %s for input %s." % (self.thread_id, self.input_name))
            
            done = False
            while not done:
                try:

                    file_pid = str(open("/tmp/%s_current.pid" % self.input_name.replace("://", "-"), "r").read())
                    #logging.debug("******** this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                    if self.getName().strip() != file_pid.strip():
                        logging.debug("$$$$ Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                        done = True
                        break
                        #sys.exit(1)
                    else:
                        pass

                    self.session = requests.Session()
                    self.session.auth = (self.rest_user, self.rest_user_password)
                    self.session.verify = False

                    #start getting the events...
                    #self.get_active_users()
                    self.last_run_time = time.time()
                    self.get_status("default", "CPUUsage", check_interval=self.cpu_usage_int)
                    self.get_status("default", "ConnectionsAccepted", check_interval=self.conns_accepted_int)

                    self.get_status("default", "TransmitKbpsThroughput", check_interval=self.tx_rx_kbps_thruput_int)
                    self.get_status("default", "ReceiveKbpsThroughput", check_interval=self.tx_rx_kbps_thruput_int)

                    self.get_status("default", "MemoryStatus", check_interval=self.memory_int)
                    self.get_status("default", "DomainsMemoryStatus", check_interval=self.memory_int)

                    if self.active_users:
                        self.get_status("default", "ActiveUsers", check_interval=self.active_users_int)
                    
                    if self.date_time_status:
                        self.get_status("default", "DateTimeStatus", field_prefix="dp_", check_interval=self.date_time_status_int)
                    
                    if self.domain_status:
                        self.get_status("default", "DomainStatus", check_interval=self.domain_status_int)
                    
                    if self.log_target_status:
                        self.get_status("default", "LogTargetStatus", check_interval=self.log_target_status_int)


                    self.get_status("default", "FilesystemStatus", check_interval=self.file_system_int)

                    self.get_status("default", "StandbyStatus", check_interval=self.network_int)

                    self.get_status("default", "EthernetInterfaceStatus", check_interval=self.network_int)
                    self.get_status("default", "EthernetCountersStatus", check_interval=self.network_int)
                    self.get_status("default", "TCPSummary", check_interval=self.network_int)

                    #self.get_status("default", "NetworkReceiveDataThroughput", check_interval=self.network_int)
                    #self.get_status("default", "NetworkReceivePacketThroughput")
                    #self.get_status("default", "NetworkTransmitDataThroughput", check_interval=self.network_int)
                    #self.get_status("default", "NetworkTransmitPacketThroughput")

                    self.get_status("default", "DocumentCachingSummaryGlobal", check_interval=self.xslt_int)
                    self.get_status("default", "SystemUsage", check_interval=self.system_usage_int)
                    self.get_status("default", "SystemUsage2Table", check_interval=self.system_usage_int)

                    self.get_status("default", "XMLNamesStatus", check_interval=self.xslt_int)

                    if self.sensors_status:
                        self.get_status("default", "VoltageSensors", check_interval=self.sensors_int)
                        self.get_status("default", "CurrentSensors", check_interval=self.sensors_int)
                        self.get_status("default", "EnvironmentalFanSensors", check_interval=self.sensors_int)
                        self.get_status("default", "EnvironmentalSensors", check_interval=self.sensors_int)

                    for domain in self.domain_list:
                        logging.debug("Getting stats for domain:" + str(domain))
                        if self.load_balancer_status:
                            self.get_status(domain, "LoadBalancerStatus2", include_domain=True, check_interval=self.load_balancer_status_int)

                        if self.object_status:
                            self.get_status(domain, "ObjectStatus", include_domain=True, check_interval=self.object_status_int)

                        if self.http_status:
                            logging.debug("before get_stats HTTPConnections self.http_int ")
                            self.get_status(domain, "HTTPConnections", include_domain=True, check_interval=self.http_int)
                            logging.debug("after get_stats HTTPConnections self.http_int ")
                            #self.get_status(domain, "HTTPMeanTransactionTime2", include_domain=True, check_interval=self.http_int)
                            #self.get_status(domain, "HTTPTransactions2", include_domain=True, check_interval=self.http_int)

                        if self.mq_status:
                            self.get_status(domain, "MQConnStatus", include_domain=True, check_interval=self.mq_int)
                            self.get_status(domain, "MQQMstatus", include_domain=True, check_interval=self.mq_int)

                        if self.sql_status:
                            self.get_status(domain, "SQLStatus", include_domain=True, check_interval=self.sql_int)
                            self.get_status(domain, "SQLConnectionPoolStatus", include_domain=True, check_interval=self.sql_int)
                            self.get_status(domain, "SQLRuntimeStatus", include_domain=True, check_interval=self.sql_int)

                        if self.service_memory_status:
                            self.get_status(domain, "ServicesMemoryStatus2", include_domain=True, check_interval=self.memory_int)

                        if self.xslt_status:
                            self.get_status(domain, "StylesheetCachingSummary", include_domain=True, check_interval=self.xslt_int)
                            self.get_status(domain, "StylesheetExecutions", include_domain=True, check_interval=self.xslt_int)
                            self.get_status(domain, "StylesheetMeanExecutionTime", include_domain=True, check_interval=self.xslt_int)

                        if self.ws_op_status:
                            self.get_status(domain, "WSOperationMetrics", include_domain=True, check_interval=self.ws_op_int)
                            #self.get_status(domain, "WSOperationsStatus", include_domain=True, check_interval=900)

                        if self.wsm_stats:
                            self.get_status(domain, "WSMAgentStatus", include_domain=True, check_interval=self.wsm_stats_int)
                            self.get_status(domain, "WSMAgentSpoolers", include_domain=True, check_interval=self.wsm_stats_int)

                        if self.web_app_fw_stats:
                            self.get_status(domain, "WebAppFwAccepted", include_domain=True, check_interval=self.web_app_fw_int)
                            self.get_status(domain, "WebAppFwRejected", include_domain=True, check_interval=self.web_app_fw_int)

                    logging.info("REST Poller finished in %s seconds." % (time.time() - self.last_run_time))
                    #self.session.close()
                        #logging.debug("!!! NOT Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                except Exception as ex:
                    logging.error("Exception occurred in RESTPoller. Stopping.  Exception: " + str(ex))
                    #sys.exit(1)
                    break
                finally:
                    #pass
                    self.session.close()
                    #break 

                time.sleep(float(self.dpinput_interval))

        def do_rest_request(self, rest_mgmt_url):

            try:
                #r = self.session.post(self.rest_url, data=req_data, auth=(self.rest_user, self.rest_user_password), verify=False)
                logging.debug("GET request to rest_mgmt_url:" + str(rest_mgmt_url))
                r = self.session.get(rest_mgmt_url)
                if r.status_code != 200:
                    logging.error("REST request failed! Status code: %i Content: %s" % (r.status_code, str(r.content)))
                    return None
                else:
                    return r.content

            except Exception as ex:
                logging.error("Exception occurred while making REST request. Exception: %s" % (str(ex)))
                return None

        def get_service_from_url(self, in_url, domain):
            tran_req_url_port = None
            tran_req_url_uri = None
            service_obj = None
            if in_url is not None:
                #logging.debug("In URL %s" % str(in_url))
                first_c = in_url.find("://")
                port_start_pos = in_url.find(":", first_c + 1)
                if port_start_pos > 0:
                    port_end_pos = in_url.find("/", port_start_pos)

                    if port_end_pos > 0:
                        tran_req_url_port = in_url[port_start_pos + 1:port_end_pos]
                        url_parms_start = in_url.find("?", port_end_pos)
                        if url_parms_start > 0:
                            tran_req_url_uri = in_url[port_end_pos:url_parms_start]
                        else:
                            tran_req_url_uri = in_url[port_end_pos:]
                else:
                    tran_req_url_port = "0"
                    first_s = in_url.find("/", first_c + 4)
                    if first_s > 0:
                        url_parms_start = in_url.find("?", first_s)
                        if url_parms_start > 0:
                            tran_req_url_uri = in_url[first_s:url_parms_start]
                        else:
                            tran_req_url_uri = in_url[first_s:]

                #logging.debug("Tran port %s and uri %s " % (tran_req_url_port, tran_req_url_uri))
                if tran_req_url_port is not None and tran_req_url_uri is not None:
                    #logging.debug("Looking up %s and uri %s " % (tran_req_url_port, tran_req_url_uri))
                    if domain in self.domain_wsm_op_dict:
                        if (tran_req_url_port, tran_req_url_uri.strip()) in self.domain_wsm_op_dict[domain]:
                            service_obj = self.domain_wsm_op_dict[domain][(tran_req_url_port, tran_req_url_uri.strip())]

            return service_obj

        def get_status(self, domain, status_class, include_domain=False, field_prefix=None, check_interval=None):

            if check_interval is not None:
                if (self.device_name, domain, status_class) in self.check_interval_dict:
                    if (self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)])  < check_interval:
                        logging.debug("Check interval of %i NOT reached(%s). Not Getting %s for device %s and domain %s." % (check_interval, self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)], status_class, self.device_name, domain))
                        return
                    else:
                        logging.debug(  "Check interval for %s of %i for device %s and domain %s reached(%s). Getting" % (status_class, check_interval, self.device_name, domain, self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)]))
                        self.check_interval_dict[(self.device_name, domain, status_class)] = self.last_run_time
                else:
                    self.check_interval_dict[(self.device_name, domain, status_class)] = self.last_run_time

            rest_mgmt_url = self.rest_mgmt_url.format(device_host=self.device_host, rest_port=self.rest_port, mgmt_uri="/mgmt/status/{domain}/{status_class}".format(domain=domain, status_class=status_class))
            event_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z")
            resp = self.do_rest_request(rest_mgmt_url)

            if resp is None:
                logging.error("Error getting %s for device %s." % (status_class, self.device_name))
                return
            
            try:
                resp_obj = json.loads(resp)
                logging.debug("resp_obj:" + str(resp_obj))
                new_obj = collections.OrderedDict()
                new_obj["time"] = ""
                new_obj["device"] = self.device_name
                if include_domain:
                    new_obj["domain"] = domain

                new_obj["status_class"] = status_class
                
                if status_class in resp_obj:
                    if isinstance(resp_obj[status_class], dict):
                        logging.debug("resp_obj[status_class], dict")
                        new_obj[status_class] = resp_obj[status_class]
                        r_i = resp_obj[status_class]
                        if status_class in ["EthernetInterfaceStatus", "EthernetCountersStatus",  "NetworkTransmitPacketThroughput", "NetworkTransmitDataThroughput", "NetworkReceivePacketThroughput", "NetworkReceiveDataThroughput"]:
                            if self.network_stats_interface_list is not None:
                                int_name = None
                                if "Name" in r_i:
                                    int_name = r_i["Name"]
                                else:
                                    if "InterfaceName" in r_i:
                                        int_name = r_i["InterfaceName"]
                                
                                if int_name in self.network_stats_interface_list:
                                    self.log_event(new_obj, event_time=event_time)    

                            else:
                                self.log_event(new_obj, event_time=event_time)    
                        else:
                            self.log_event(new_obj, event_time=event_time)
                    else:
                        if isinstance(resp_obj[status_class], list):
                            logging.debug("resp_obj[status_class], list")
                            for r_i in resp_obj[status_class]:
                                new_obj = collections.OrderedDict()
                                new_obj["time"] = ""
                                new_obj["device"] = self.device_name
                                if include_domain:
                                    new_obj["domain"] = domain

                                new_obj["status_class"] = status_class
                                new_obj[status_class] = r_i
                                
                                if status_class in ["EthernetInterfaceStatus", "EthernetCountersStatus",  "NetworkTransmitPacketThroughput", "NetworkTransmitDataThroughput", "NetworkReceivePacketThroughput", "NetworkReceiveDataThroughput"]:
                                    if self.network_stats_interface_list is not None:
                                        int_name = None
                                        if "Name" in r_i:
                                            int_name = r_i["Name"]
                                        else:
                                            if "InterfaceName" in r_i:
                                                int_name = r_i["InterfaceName"]
                                
                                        if int_name in self.network_stats_interface_list:
                                            self.log_event(new_obj, event_time=event_time)    

                                    else:
                                        self.log_event(new_obj, event_time=event_time)    
                                else:
                                    self.log_event(new_obj, event_time=event_time)
                            
                        else:
                            new_obj = collections.OrderedDict()
                            new_obj["time"] = ""
                            new_obj["device"] = self.device_name
                            if include_domain:
                                new_obj["domain"] = domain

                            new_obj["status_class"] = status_class
                            new_obj[status_class] = resp_obj[status_class]
                            self.log_event(new_obj, event_time=event_time)

                else:
                    logging.debug("No %s results on device %s and domain %s." % (status_class, self.device_name, domain))

            except Exception as ex:
                logging.error("Exception occurred while %s for device %s and domain %s.  Exception: %s" % (status_class, self.device_name, domain, str(ex)))
  
    def do_run(self, input_name, input_item, ew):
        
        domain_wsm_op_dict = {}
        self.rest_mgmt_url = "https://{device_host}:{rest_port}{mgmt_uri}"
        #logging.debug("... DPINPUT: do_run() ...")
        
        input_name =  input_name
        device_name = input_item["device_name"]
        device_host = input_item["device_host"]
        rest_port = int(input_item["rest_port"])
        rest_user = input_item["rest_user"]
        rest_user_password = input_item["rest_user_password"]
        enable_stats = int(input_item["enable_stats"])
        enable_stats_domains = None
        if "enable_stats_domains" in input_item:
            enable_stats_domains = input_item["enable_stats_domains"]
        only_eth_ints_with_ips = input_item["only_eth_ints_with_ips"]
            
        # wsm_msg_payloads_mongodb_client = None

        if (device_host is None) or (rest_port is None) or (rest_user is None) or (rest_user_password is None):
            logging.error("Device host, REST port, user or password is None?   Stopping.")
            return

        rest_session = None
        network_stats_interface_list = None
        enable_stats_domain_list = None
        #wsm_domain_list = None
        enable_stats_domain_list = None
        #wsm_domain_list = None
        domain_list = None
 
        if enable_stats_domains is not None:
            enable_stats_domain_list = list(map(str,enable_stats_domains.split(",")))
            enable_stats_domain_list = [x.strip(' ') for x in enable_stats_domain_list]

        # if wsm_domains is not None:
        #     wsm_domain_list = list(map(str,wsm_domains.split(",")))
        #     wsm_domain_list = [x.strip(' ') for x in wsm_domain_list]

        try:
            device_comms_ok = False
            sleep_time = 900
            while(device_comms_ok == False):

                logging.info("Creating REST session to device %s (%s:%s)." % (device_name, device_host, rest_port))
                rest_session = requests.Session()
                rest_session.auth = (rest_user, rest_user_password)
                rest_session.verify = False

                domain_list = None

                domain_list = self.get_domains(rest_session, device_host, rest_port, rest_user, rest_user_password)
                if domain_list is not None:
                    if len(domain_list) > 0:
                        device_comms_ok = True
                        break

                logging.error("Unable to get domain list for device %s." % (device_name))
                logging.error("Will try again at in %i seconds." % (sleep_time))

                if rest_session is not None:
                    rest_session.close()

                time.sleep(sleep_time)

            logging.debug("Communication to device %s ok." % device_name)

            if enable_stats:

                if enable_stats_domain_list is None:
                    enable_stats_domain_list = domain_list

                for domain in enable_stats_domain_list:
                    if self.get_config_enabled(rest_session, device_host, rest_port, rest_user, rest_user_password, domain, "Statistics"):
                        logging.debug("Statistics already enabled for domain %s." % domain)
                    else:
                        if not self.enable_statistics_domain(rest_session, device_host, rest_port, rest_user, rest_user_password, domain):
                            logging.error("Enable statistics for domain %s failed!" % domain)
                        else:
                            logging.debug("Enabled statistics for domain %s." % domain)

            if domain_list is not None:
                for domain in domain_list:
                    ws_op_dict = self.get_ws_operations_status(rest_session, device_host, domain, rest_port, rest_user, rest_user_password)
                    domain_wsm_op_dict[domain] = ws_op_dict

            #logging.debug("WS Op dict for domain %s is %s" % (domain, ws_op_dict))

            if only_eth_ints_with_ips > 0:
                network_stats_interface_list = self.get_eth_ints_with_ips(rest_session, device_host, "default", rest_port, rest_user, rest_user_password)

            rest_session.close()
            thread_id = str(uuid.uuid4())
            pid_fle = open("/tmp/%s_current.pid" % input_name.replace("://", "-"), "w")
            pid_fle.write(thread_id)
            pid_fle.close()

            logging.debug("Starting thread %s for %s." % (thread_id, input_name.replace("://", "-")))
            rest_t = self.RESTPollerThread(thread_id, input_name, input_item, ew, domain_wsm_op_dict, domain_list, network_stats_interface_list)
            rest_t.start()

        except Exception as ex:
            logging.error("Unhandled Exception occurred in do_run. Exception:" + str(ex))

    def stream_events(self, inputs, ew):
        # Splunk Enterprise calls the modular input, 
        # streams XML describing the inputs to stdin,
        # and waits for XML on stdout describing events.
        logging.debug(str(inputs))
        logging.debug(str(inputs.inputs ))
        for input_name, input_item in inputs.inputs.iteritems():
            self.do_run(input_name, input_item, ew)

if __name__ == "__main__":
    sys.exit(DPStatsInput().run(sys.argv))
             