'''
IBM Websphere Datapower Modular Input for Splunk
Hannes Wagener - 2016

Used the Splunk provided modular input as example.

DISCLAIMER
You are free to use this code in any way you like, subject to the
Python & IBM disclaimers & copyrights. I make no representations
about the suitability of this software for any purpose. It is
provided "AS-IS" without warranty of any kind, either express or
implied.

'''
import requests
import os
import lxml.etree
import sys
import logging
import xml.dom.minidom
import xml.sax.saxutils
import time
import threading
import uuid
import cgi
import datetime
import cherrypy
import base64
import zlib
import re
try:
    import pymongo
except:
    pass


SPLUNK_HOME = os.environ.get("SPLUNK_HOME")
MONGODB_AUTH_DB = "admin"
# Initialize the root logger with a StreamHandler and a format message:
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

SCHEME = """<scheme>
    <title>IBM Websphere Datapower</title>
    <description>IBM Websphere Datapower Input for Splunk</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>false</use_single_instance>

    <endpoint>
        <args>
            <arg name="name">
                <title>Device Name</title>
                <description>Name of the Datapower device to monitor.</description>
            </arg>
            <arg name="device_host">
                <title>Datapower Device Hostname or IP</title>
                <description>IP or hostname of the Datapower device to be monitored.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="soma_port">
                <title>SOMA Port</title>
                <description>The XML Management interface(SOMA) port number.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="soma_user">
                <title>The SOMA user</title>
                <description>The user to use when using the XML Management Interface.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
             <arg name="soma_user_password">
                <title>The SOMA user's password</title>
                <description>The users password</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="dpinput_interval">
                <title>Interval</title>
                <description>How often to run the MQ input script. Defaults to 60 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="cpu_usage_int">
                <title>CPU Usage Interval</title>
                <description>How often to capture CPU usage statistics. Defaults to 60 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="conns_accepted_int">
                <title>Connections Accepted Interval</title>
                <description>How often to capture Connection Accepted statistics. Defaults to 60 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="memory_int">
                <title>Memory Usage Interval</title>
                <description>How often to capture Memory usage statistics. Defaults to 300 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="tx_rx_kbps_thruput_int">
                <title>Network Transmit and Receive Kbps Interval</title>
                <description>How often to capture Network Transmit and Receive Kbps statistics. Defaults to 60 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="network_int">
                <title>Network Statistics Interval</title>
                <description>How often to capture Network and TCP related statistics. Defaults to 300 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

           <arg name="system_usage_int">
                <title>System Usage Interval</title>
                <description>How often to capture System usage statistics. Defaults to 300 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="enable_stats">
                <title>Enable statistics gathering.</title>
                <description>Enable statistics gathering.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="enable_stats_domains">
                <title>Enable statistics gathering in the listed domains.</title>
                <description>Enable statistics gathering in the listed domains. Empty will enable for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="only_eth_ints_with_ips">
                <title>Ethernet Interfaces with IP's only.</title>
                <description>Capture network statistics for interfaces with IP's only.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="object_status">
                <title>Capture Object Status</title>
                <description>Capture Object Status. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="object_status_int">
                <title>Capture Object Status Interval</title>
                <description>How often to capture object status output. Defaults to 900 seconds.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="http_status">
                <title>Capture HTTP statistics</title>
                <description>Capture HTTP related statistics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="http_int">
                <title>HTTP statistics interval</title>
                <description>How often to capture HTTP related statistics. Defaults to 60.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="service_memory_status">
                <title>Capture Service Memory statistics</title>
                <description>Capture Service memory statistics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="sql_status">
                <title>Capture SQL statistics.</title>
                <description>Capture SQL related statistics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="sql_int">
                <title>SQL statistics interval</title>
                <description>How often to capture SQL related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="mq_status">
                <title>Capture Websphere MQ statistics.</title>
                <description>Capture Websphere MQ related statistics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="mq_int">
                <title>MQ statistics interval</title>
                <description>How often to capture MQ related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="sensors_status">
                <title>Capture Hardware and sensor statistics</title>
                <description>Capture Hardware and other sensor statistics. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="sensors_int">
                <title>Hardware and Sensor statistics interval</title>
                <description>How often to capture Hardware and Sensor related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="xslt_status">
                <title>Capture XSLT statistics</title>
                <description>Capture XSLT related statistics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="xslt_int">
                <title>XSLT and XML statistics interval</title>
                <description>How often to capture XSLT and XML related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="ws_op_status">
                <title>Capture Web service operation metrics.</title>
                <description>Capture Web service operation metrics. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="ws_op_status_int">
                <title>Web servce operation statistics interval</title>
                <description>How often to capture web service operation related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>



            <arg name="web_app_fw_stats">
                <title>Capture WebAppFw accepted and rejected statistics.</title>
                <description>Capture WebAppFw accepted and rejected statistics.. Will capture statistics for all domains.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="web_app_fw_int">
                <title>WebAppFw statistics interval</title>
                <description>How often to capture WebAppFw related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>



            <arg name="use_wsm">
                <title>Use WS-M to capture transaction statistics.</title>
                <description>Use WS-M to capture transaction statistics. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_stats_int">
                <title>WSM Agent and spoolers statistics interval</title>
                <description>How often to capture WSM Agent and spoolers related statistics. Defaults to 300.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="enable_wsm">
                <title>Enable the WS-M agents on the device.</title>
                <description>Enable the WS-M agents on the device.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_domains">
                <title>Use WS-M to capture transaction statistics.</title>
                <description>Use WS-M to capture transaction statistics. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="use_wsm_transaction_time">
                <title>Use WS-M transaction time as event time</title>
                <description>Use WS-M transaction time as event time.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="wsm_max_rec_size">
                <title>WS-M maximum record size.</title>
                <description>WS-M maximum record size. Defaults to 3000.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="wsm_max_mem">
                <title>WS-M maximum memory.</title>
                <description>WS-M maximum memory. Defaults to 64mb.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_capture_mode">
                <title>WS-M capture mode.</title>
                <description>WS-M capture mode.All, faults or none. Defaults to All.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_buf_mode">
                <title>WS-M buffering mode.</title>
                <description>WS-M buffering mode.  Discard or Buffer. Defaults to Buffer. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_med_enf_metrics">
                <title>WS-M mediation enforcement metrics.</title>
                <description>Capture WS-M mediation enforcement metrics. Defaults to false.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>



            <arg name="wsm_pull">
                <title>WS-M pull subscription.</title>
                <description>WS-M pull subscription.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_interval">
                <title>WS-M pull interval.</title>
                <description>WS-M pull interval. Defaults to 60.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_max_soap_env_size">
                <title>WS-M pull maximum SOAP Envelop size.</title>
                <description>WS-M pull maximum SOAP Envelop size.  Defaults to 511.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_max_elements">
                <title>WS-M pull maximum number of elements.</title>
                <description>The maximum number of elements to return on a pull request.  Defaults to 100.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_use_custom_formatter">
                <title>se the custom Splunk WSM formatter to format the WSM data on the device.</title>
                <description>se the custom Splunk WSM formatter to format the WSM data on the device.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push">
                <title>WS-M push subscription.</title>
                <description>WS-M push subscription.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_host">
                <title>WS-M push server host.</title>
                <description>The host to use for the server to which the WS-M data will be pushed to. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_port">
                <title>WS-M push server port.</title>
                <description>The port to use for the server to which the WS-M data will be pushed to. Defaults to 14014.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_thread_per_domain">
                <title>WS-M Push server thread per domain.</title>
                <description>Start a WS-M Push server thread per domain.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_max_elements">
                <title>WS-M push maximum number of elements.</title>
                <description>The maximum number of elements to send on the push request.  Defaults to 100.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="wsm_msg_payloads_to_disk">
                <title>Write WS-M message payloads to disk instead of indexing in Splunk</title>
                <description>Write WS-M message payloads to disk instead of indexing in Splunk.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_folder">
                <title>Folder to write message payloads to.</title>
                <description>Write WS-M message payloads to disk instead of indexing in Splunk.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_use_mongodb">
                <title>Write payloads to a Mongo database.</title>
                <description>Write payloads to a Mongo database instead of writing individual files.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_db_name">
                <title>The mongodb database name.</title>
                <description>The mongodb database to use.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_host">
                <title>The mongodb server host name.</title>
                <description>The mongodb server host name.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_port">
                <title>The mongodb server port.</title>
                <description>The mongodb server port.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_use_auth">
                <title>Use mongodb authorisation.</title>
                <description>Use mongodb authorisation.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_user">
                <title>The mongodb database user.</title>
                <description>The mongodb database to insert the payloads into.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

         <arg name="wsm_msg_payloads_mongodb_password">
                <title>The mongodb user password.</title>
                <description>The mongodb user password.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

        </args>
    </endpoint>
</scheme>
"""

def do_validate():

    try:
        config = get_validation_config()

        device_host = config.get("device_host")
        soma_port = config.get("soma_port")
        soma_user = config.get("soma_user")
        soma_user_password = config.get("soma_user_password")
        dpinput_interval = config.get("dpinput_interval")

        validationFailed = False

        if device_host is None:
            print_validation_error("Device host is mandatory.")
            validationFailed = True

        if soma_port is None or int(soma_port) < 1:
            print_validation_error("SOMA Port value must be a positive integer")
            validationFailed = True

        if soma_user is None:
            print_validation_error("SOMA User name is mandatory.")
            validationFailed = True

        if soma_user_password is None:
            print_validation_error("SOMA User password name is mandatory.")
            validationFailed = True

        if not dpinput_interval is None and int(dpinput_interval) < 1:
            print_validation_error("Script polling interval must be a positive integer")
            validationFailed = True

        if validationFailed:
            sys.exit(2)

    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        logging.error("Exception getting XML configuration: %s" % str(e))
        sys.exit(1)
        raise

get_status_req = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
    <env:Body>
        <dp:request domain="{domain}" xmlns:dp="http://www.datapower.com/schemas/management">
            <dp:get-status class="{status_class}"/>
        </dp:request>
    </env:Body>
</env:Envelope>
"""

soma_url = "https://{device_host}:{soma_port}/service/mgmt/3.0"

def get_domains(soma_session, device_host, soma_port, soma_user, soma_user_password):
    domain_status = {"domain": "default", "status_class": "DomainStatus"}
    domain_status_req = get_status_req.format(**domain_status)

    logging.debug("Getting domains from " + device_host)

    domain_list = None
    try:
        #r = requests.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_status_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_status_req)

        if r.status_code != 200:
            logging.error("Get of domains for %s failed.  Status code: %i." % (device_host, r.status_code))
            return None
        else:
            logging.debug("Get of domains for %s OK!.  Status code: %i." % (device_host, r.status_code))

        doc = lxml.etree.fromstring(r.content)

        d_nl = doc.xpath("//Domain")

        if len(d_nl) > 0:
            domain_list = []
            for d in d_nl:
                domain_list.append(d.text)

    except Exception, ex:
        logging.error("Exception occurred while getting domains. Exception: " + str(ex))

    return domain_list

def get_ws_operations_status(soma_session, device_host, domain, soma_port, soma_user, soma_user_password):
    wsop_status = {"domain": domain, "status_class": "WSOperationsStatus"}
    wsop_status_req = get_status_req.format(**wsop_status)

    #logging.debug("Getting WSOP Status for " + device_host + " and domain " + domain)

    ws_op_dict = {}
    try:
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=wsop_status_req)

        if r.status_code != 200:
            logging.error("Get of WS operation status failed for device %s and domain %s failed.  Status code: %i." % (device_host, domain,  r.status_code))
            return None
        else:
            pass
            #logging.debug("Get of WS operation status for device %s and domain %s OK!.  Status code: %i." % (device_host, domain, r.status_code))

        doc = lxml.etree.fromstring(r.content)

        d_nl = doc.xpath("//WSOperationsStatus")

        if len(d_nl) > 0:
            for d_n in d_nl:
                port_n = d_n.find("Port")
                url_n = d_n.find("URL")
                wsg_n = d_n.find("WSGateway")

                if port_n is not None and url_n is not None and wsg_n is not None:
                    ws_op_dict[(port_n.text.strip(), url_n.text.strip())] = wsg_n.text
                else:
                    logging.debug("WSOp status no Port, url or wsgateway found???")
        else:
            pass
            #logging.debug("No WSOperationsStatus resultS??")

    except Exception, ex:
        logging.error("Exception occurred while getting domains. Exception: " + str(ex))

    return ws_op_dict

def get_eth_ints_with_ips(soma_session, device_host, domain, soma_port, soma_user, soma_user_password):
    ip_status = {"domain": domain, "status_class": "IPAddressStatus"}
    ip_status_req = get_status_req.format(**ip_status)

    #logging.debug("Getting IPAddressStatus Status for " + device_host + " and domain " + domain)

    network_stats_interface_list = None
    try:
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=ip_status_req)

        if r.status_code != 200:
            logging.error("Get ofIPAddressStatus failed for device %s and domain %s failed.  Status code: %i." % (device_host, domain,  r.status_code))
            return None
        else:
            pass
            #logging.debug("Get of IPAddressStatus for device %s and domain %s OK!.  Status code: %i." % (device_host, domain, r.status_code))

        doc = lxml.etree.fromstring(r.content)

        d_nl = doc.xpath("//IPAddressStatus")

        if len(d_nl) > 0:
            network_stats_interface_list = []
            for d_n in d_nl:
                name_n = d_n.find("Name")
                name_n_t = name_n.text
                if name_n.text is not None:
                    if name_n is not None:
                        if name_n_t.strip() not in network_stats_interface_list:
                            network_stats_interface_list.append(name_n_t)
                    else:
                        logging.error("Huh?? Interface Name is none?")
        else:
            logging.error("No IPAddressStatus results?")

    except Exception, ex:
        logging.error("Exception occurred while getting domains. Exception: " + str(ex))

    return network_stats_interface_list



save_config_req = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <dp:request domain="{domain}" xmlns:dp="http://www.datapower.com/schemas/management">
         <dp:do-action>
            <SaveConfig />
         </dp:do-action>
      </dp:request>
   </soapenv:Body>
</soapenv:Envelope>
"""

def save_config(soma_session, device_host, soma_port, soma_user, soma_user_password, domain):
    domain_save_config_req = save_config_req.format(domain=domain)

    try:
        #r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_save_config_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_save_config_req)

        if r.status_code != 200:
            logging.error("Request to save config for domain %s failed.  Status code: %i." % (domain, r.status_code))
            return False
        else:
            logging.debug("Request to save config for domain %s Ok.  Status code: %i." % (domain, r.status_code))

        nss = {"dp": "http://www.datapower.com/schemas/management"}

        doc = lxml.etree.fromstring(r.content)

        res_nl = doc.xpath("//dp:result", namespaces=nss)

        if len(res_nl) > 0:
            if res_nl[0].text.strip().upper() == "OK":
                return True
            else:
                return False
        else:
            logging.error("Could not find dp:result tag??")
            return False
    except Exception, ex:
        logging.error("Exception occured while saving config for host %s and domain %s.  Exception: %s" % (device_host, domain, str(ex)))
        return False

get_config_req = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:man="http://www.datapower.com/schemas/management">
   <soapenv:Header/>
   <soapenv:Body>
      <man:request domain="{domain}">
         <man:get-config class="{config_class}" />
      </man:request>
   </soapenv:Body>
</soapenv:Envelope>
"""



def get_config_enabled(soma_session, device_host, soma_port, soma_user, soma_user_password, domain, config_class):

    try:
        soma_get_config_req = get_config_req.format(domain=domain, config_class=config_class)

        #r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_enable_stats_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=soma_get_config_req)

        if r.status_code != 200:
            logging.error("Request to get %s for domain %s failed.  Status code: %i." % (config_class, domain, r.status_code))
            return None
        else:
            pass
            #logging.debug("Request to get %s for domain %s Ok.  Status code: %i." % (config_class, domain, r.status_code))

        nss = {"dp": "http://www.datapower.com/schemas/management"}

        doc = lxml.etree.fromstring(r.content)

        res_nl = doc.xpath("//%s" % config_class)

        if len(res_nl) > 0:
            admin_stat_n = res_nl[0].find("mAdminState")
            if admin_stat_n is not None:
                if admin_stat_n.text is not None:
                    if admin_stat_n.text == "enabled":
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            logging.error("Could not find %s tag??" % config_class)
            return False
    except Exception, ex:
        logging.error("Exception occurred while getting %s for host %s and domain %s.  Exception: %s" % (config_class, device_host, domain, str(ex)))
        return False


enable_statistics_req = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:man="http://www.datapower.com/schemas/management">
   <soapenv:Header/>
   <soapenv:Body>
      <man:request domain="{domain}">
         <man:set-config>
            <Statistics>
               <mAdminState>enabled</mAdminState>
               <LoadInterval>1000</LoadInterval>
            </Statistics>
         </man:set-config>
      </man:request>
   </soapenv:Body>
</soapenv:Envelope>
"""


def enable_statistics_domain(soma_session, device_host, soma_port, soma_user, soma_user_password, domain):

    try:
        domain_enable_stats_req = enable_statistics_req.format(domain=domain)

        #r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_enable_stats_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_enable_stats_req)

        if r.status_code != 200:
            logging.error("Request to enable of stats for domain %s failed.  Status code: %i." % (domain, r.status_code))
            return None
        else:
            pass
            #logging.debug("Request to enable of stats for domain %s Ok.  Status code: %i." % (domain, r.status_code))

        nss = {"dp": "http://www.datapower.com/schemas/management"}

        doc = lxml.etree.fromstring(r.content)

        res_nl = doc.xpath("//dp:result", namespaces=nss)

        if len(res_nl) > 0:
            if res_nl[0].text.strip().upper() == "OK":
                return save_config(soma_session, device_host, soma_port, soma_user, soma_user_password, domain)
            else:
                return False
        else:
            logging.error("Could not find dp:result tag??")
            return False
    except Exception, ex:
        logging.error("Exception occurred while enableling statistics for host %s and domain %s.  Exception: %s" % (device_host, domain, str(ex)))
        return False


enable_wsm_req = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:man="http://www.datapower.com/schemas/management">
   <soapenv:Header/>
   <soapenv:Body>
      <man:request domain="{domain}">
         <man:set-config>
            <WebServicesAgent>
               <mAdminState>enabled</mAdminState>
               <UserSummary>Enabled from Splunk</UserSummary>
               <MaxRecords>{max_recs}</MaxRecords>
               <MaxMemoryKB>{max_mem}</MaxMemoryKB>
               <CaptureMode>{capture_mode}</CaptureMode>
               <BufferMode>{buffer_mode}</BufferMode>
               <MediationMetrics>{med_metrics}</MediationMetrics>
            </WebServicesAgent>
         </man:set-config>
      </man:request>
   </soapenv:Body>
</soapenv:Envelope>
"""


def enable_wsm_domain(soma_session, device_host, soma_port, soma_user, soma_user_password, domain, wsm_max_rec_size, wsm_max_mem, wsm_capture_mode, wsm_buf_mode, wsm_med_enf_metrics):

    try:
        wsm_med_on_off = "off"
        if wsm_med_enf_metrics == 1:
            wsm_med_on_off = "on"
        domain_enable_wsm_req = enable_wsm_req.format(domain=domain,max_recs=wsm_max_rec_size, max_mem=wsm_max_mem, capture_mode=wsm_capture_mode, buffer_mode=wsm_buf_mode, med_metrics=wsm_med_on_off)
        #r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_enable_wsm_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_enable_wsm_req)

        if r.status_code != 200:
            logging.error("Request to enable WS-M for domain %s failed.  Status code: %i. Content: %s Request: %s" % (domain, r.status_code, r.content, domain_enable_wsm_req))
            return False
        else:
            logging.debug("Request to enable WS-M for domain %s Ok.  Status code: %i." % (domain, r.status_code))

        nss = {"dp": "http://www.datapower.com/schemas/management"}

        doc = lxml.etree.fromstring(r.content)

        res_nl = doc.xpath("//dp:result", namespaces=nss)

        if len(res_nl) > 0:
            if res_nl[0].text.strip().upper() == "OK":
                return save_config(soma_session, device_host, soma_port, soma_user, soma_user_password, domain)
            else:
                return False
        else:
            logging.error("Could not find dp:result tag??")
            return False
    except Exception, ex:
        logging.error("Exception occurred while enableling ws-m for host %s and domain %s.  Exception: %s" % (device_host, domain, str(ex)))
        return False

wsm_pull_threads = []
domain_wsm_op_dict = {}
def do_run():

    #logging.debug("... DPINPUT: do_run() ...")

    config = get_input_config()

    splunk_host = config.get("host")
    input_name =  config.get("name")
    device_name = config.get("device_name")
    device_host = config.get("device_host")
    soma_port = int(config.get("soma_port",5550))
    soma_user = config.get("soma_user")
    soma_user_password = config.get("soma_user_password")
    dpinput_interval = float(config.get("dpinput_interval",60))
    cpu_usage_int = float(config.get("cpu_usage_int",60))
    conns_accepted_int = float(config.get("conns_accepted_int",60))
    memory_int = float(config.get("memory_int",300))
    tx_rx_kbps_thruput_int = float(config.get("tx_rx_kbps_thruput_int",60))
    network_int = float(config.get("network_int",300))
    system_usage_int = float(config.get("system_usage_int",300))
    enable_stats = int(config.get("enable_stats",0))
    enable_stats_domains = config.get("enable_stats_domains")
    only_eth_ints_with_ips = int(config.get("only_eth_ints_with_ips",0))

    object_status = int(config.get("object_status",0))
    object_status_int = float(config.get("object_status_int",900))

    http_status = int(config.get("http_status",0))
    http_int = float(config.get("http_int",60))

    service_memory_status = int(config.get("service_memory_status",0))
    sql_status = int(config.get("sql_status",0))
    sql_int = float(config.get("sql_int",300))
    mq_status = int(config.get("mq_status",0))
    mq_int = float(config.get("mq_int",300))
    sensors_status = int(config.get("sensors_status",0))
    sensors_int = float(config.get("sensors_int",300))

    xslt_status = int(config.get("xslt_status",0))
    xslt_int = float(config.get("xslt_int",300))

    ws_op_status = int(config.get("ws_op_status",0))
    ws_op_int = float(config.get("ws_op_int",300))

    web_app_fw_stats = int(config.get("web_app_fw_stats",0))
    web_app_fw_int = float(config.get("web_app_fw_int",300))

    use_wsm = int(config.get("use_wsm",0))
    wsm_stats_int = float(config.get("wsm_stats_int",300))

    enable_wsm = int(config.get("enable_wsm",0))
    wsm_domains = config.get("wsm_domains")
    use_wsm_transaction_time = int(config.get("use_wsm_transaction_time",0))
    wsm_max_rec_size = int(config.get("wsm_max_rec_size",3000))
    wsm_max_mem = int(config.get("wsm_max_mem",64000))
    wsm_capture_mode = config.get("wsm_capture_mode", "faults")
    wsm_buf_mode = config.get("wsm_buf_mode", "discard")
    wsm_med_enf_metrics = int(config.get("wsm_med_enf_metrics",0))
    wsm_pull = int(config.get("wsm_pull",0))
    wsm_pull_interval = int(config.get("wsm_pull_interval",60))
    wsm_pull_max_soap_env_size = int(config.get("wsm_pull_max_soap_env_size",51200))
    wsm_pull_max_elements = int(config.get("wsm_pull_max_elements",10))
    wsm_pull_use_custom_formatter = int(config.get("wsm_pull_use_custom_formatter",0))
    wsm_push = int(config.get("wsm_push",0))
    wsm_push_server_host = config.get("wsm_push_server_host")
    wsm_push_server_port = int(config.get("wsm_push_server_port",14014))
    wsm_push_server_thread_per_domain = int(config.get("wsm_push_server_thread_per_domain",0))
    wsm_push_max_elements = int(config.get("wsm_push_max_elements",100))
    wsm_msg_payloads_to_disk = int(config.get("wsm_msg_payloads_to_disk",0))
    wsm_msg_payloads_folder = config.get("wsm_msg_payloads_folder", "/opt/splunk/dptrans")
    wsm_msg_payloads_use_mongodb = int(config.get("wsm_msg_payloads_use_mongodb",0))
    wsm_msg_payloads_mongodb_db_name = config.get("wsm_msg_payloads_mongodb_db_name", "dptrans")
    wsm_msg_payloads_mongodb_host = config.get("wsm_msg_payloads_mongodb_host", "127.0.0.1")
    wsm_msg_payloads_mongodb_port = int(config.get("wsm_msg_payloads_mongodb_port", 27017))
    wsm_msg_payloads_mongodb_use_auth = int(config.get("wsm_msg_payloads_mongodb_use_auth",0))
    wsm_msg_payloads_mongodb_user = config.get("wsm_msg_payloads_mongodb_user", "splunk")
    wsm_msg_payloads_mongodb_password = config.get("wsm_msg_payloads_mongodb_password")

    wsm_msg_payloads_mongodb_client = None

    if (device_host is None) or (soma_port is None) or (soma_user is None) or (soma_user_password is None):
        logging.error("Device host, SOMA port, user or password is None?   Stopping.")
        return

    soma_session = None
    network_stats_interface_list = None
    enable_stats_domain_list = None
    wsm_domain_list = None
    enable_stats_domain_list = None
    wsm_domain_list = None
    domain_list = None

    if enable_stats_domains is not None:
        enable_stats_domain_list = map(str,enable_stats_domains.split(","))
        enable_stats_domain_list = [x.strip(' ') for x in enable_stats_domain_list]

    if wsm_domains is not None:
        wsm_domain_list = map(str,wsm_domains.split(","))
        wsm_domain_list = [x.strip(' ') for x in wsm_domain_list]

    try:
        device_comms_ok = False
        sleep_time = 900
        while(device_comms_ok == False):

            logging.info("Creating SOMA session to device %s (%s:%s)." % (device_name, device_host, soma_port))
            soma_session = requests.Session()
            soma_session.auth = (soma_user, soma_user_password)
            soma_session.verify = False

            domain_list = None

            domain_list = get_domains(soma_session, device_host, soma_port, soma_user, soma_user_password)
            if domain_list is not None:
                if len(domain_list) > 0:
                    device_comms_ok = True
                    break

            logging.error("Unable to get domain list for device %s." % (device_name))
            logging.error("Will try again at in %i seconds." % (sleep_time))


            if soma_session is not None:
                soma_session.close()

            time.sleep(sleep_time)

        logging.debug("Communication to device %s ok." % device_name)

        if enable_stats:

            if enable_stats_domain_list is None:
                enable_stats_domain_list = domain_list

            for domain in enable_stats_domain_list:
                if get_config_enabled(soma_session, device_host, soma_port, soma_user, soma_user_password, domain, "Statistics"):
                    logging.debug("Statistics already enabled for domain %s." % domain)
                else:
                    if not enable_statistics_domain(soma_session, device_host, soma_port, soma_user, soma_user_password, domain):
                        logging.error("Enable statistics for domain %s failed!" % domain)
                    else:
                        logging.debug("Enabled statistics for domain %s." % domain)

        ws_op_dict = {}
        if (use_wsm > 0) and (enable_wsm > 0):
            if wsm_domain_list is None:
                wsm_domain_list = domain_list

            for domain in wsm_domain_list:

                if get_config_enabled(soma_session, device_host, soma_port, soma_user, soma_user_password, domain, "WebServicesAgent"):
                    logging.debug("WebServicesAgent already enabled for domain %s." % domain)
                else:

                    if not enable_wsm_domain(soma_session, device_host, soma_port, soma_user, soma_user_password, domain, wsm_max_rec_size, wsm_max_mem, wsm_capture_mode, wsm_buf_mode, wsm_med_enf_metrics):
                        logging.error("Enable WS-M for domain %s failed!" % domain)
                    else:
                        logging.debug("Enabled WS-M for domain %s." % domain)

                ws_op_dict = get_ws_operations_status(soma_session, device_host, domain, soma_port, soma_user, soma_user_password)
                domain_wsm_op_dict[domain] = ws_op_dict
                #logging.debug("WS Op dict for domain %s is %s" % (domain, ws_op_dict))

        if only_eth_ints_with_ips > 0:
            network_stats_interface_list = get_eth_ints_with_ips(soma_session, device_host, domain, soma_port, soma_user, soma_user_password)

        soma_session.close()
        thread_id = str(uuid.uuid4())
        pid_fle = open("/tmp/%s_current.pid" % input_name.replace("://", "-"), "w")
        pid_fle.write(thread_id)
        pid_fle.close()

        #logging.debug("Starting thread %s for %s." % (thread_id, input_name.replace("://", "-")))
        soma_t = SOMAPollerThread(thread_id, input_name, splunk_host, device_name,
                                  device_host, soma_port, soma_user, soma_user_password, dpinput_interval,
                                  cpu_usage_int, conns_accepted_int, memory_int,
                                  network_stats_interface_list, tx_rx_kbps_thruput_int, network_int, system_usage_int, object_status, object_status_int,
                                  http_status, http_int, service_memory_status, sql_status, sql_int, mq_status,mq_int,
                                  sensors_status, sensors_int, xslt_status, xslt_int, ws_op_status, ws_op_int,
                                  web_app_fw_stats, web_app_fw_int, use_wsm, wsm_stats_int, ws_op_dict, domain_list)
        soma_t.start()

        if use_wsm:
            if wsm_msg_payloads_folder is None:
                wsm_msg_payloads_folder = "/opt/splunk/wsm_msgs"
            else:
                if wsm_msg_payloads_folder == "":
                    wsm_msg_payloads_folder = "/opt/splunk/wsm_msgs"

            if wsm_push:
                wsm_push_threads = []
                if wsm_push_server_thread_per_domain > 0:

                    for domain in wsm_domain_list:
                        thread_id = str(uuid.uuid4())
                        pid_fle = open("/tmp/%s_wsm_%s_current.pid" % (input_name.replace("://", "-"), "main"), "w")
                        pid_fle.write(thread_id)
                        pid_fle.close()
                        pid_fle = open("/tmp/%s_wsm_%s_current.pid" % (input_name.replace("://", "-"), domain), "w")
                        pid_fle.write(thread_id)
                        pid_fle.close()
                        #with WSMPushServerThread(thread_id, domain, input_name, splunk_host, device_name, device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port, use_wsm_transaction_time, wsm_push_max_elements, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb, [domain]) as wsm_push_t:
                        wsm_push_t = WSMPushServerThread(thread_id, domain, input_name, splunk_host, device_name, device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port, use_wsm_transaction_time, wsm_push_max_elements, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb, [domain])
                        wsm_push_t.start()
                        wsm_push_threads.append(wsm_push_t)
                        wsm_push_server_port = wsm_push_server_port + 1
                else:

                    thread_id = str(uuid.uuid4())
                    pid_fle = open("/tmp/%s_wsm_%s_current.pid" % (input_name.replace("://", "-"), "main"), "w")
                    pid_fle.write(thread_id)
                    pid_fle.close()
                    for domain in domain_list:
                        pid_fle = open("/tmp/%s_wsm_%s_current.pid" % (input_name.replace("://", "-"), domain), "w")
                        pid_fle.write(thread_id)
                        pid_fle.close()

                    #with WSMPushServerThread(thread_id, "main", input_name, splunk_host, device_name, device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port, use_wsm_transaction_time, wsm_push_max_elements, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb,  wsm_domain_list) as wsm_push_t:
                    wsm_push_t = WSMPushServerThread(thread_id, "main", input_name, splunk_host, device_name, device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port, use_wsm_transaction_time, wsm_push_max_elements, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb,  wsm_domain_list)
                    wsm_push_t.start()
                    wsm_push_threads.append(wsm_push_t)
            else:
                if wsm_pull:

                    if wsm_msg_payloads_use_mongodb > 0:
                        logging.debug("Creating Mongo client to %s:%s." % (wsm_msg_payloads_mongodb_host, wsm_msg_payloads_mongodb_port))
                        wsm_msg_payloads_mongodb_client = pymongo.MongoClient(wsm_msg_payloads_mongodb_host, wsm_msg_payloads_mongodb_port)
                        if wsm_msg_payloads_mongodb_use_auth > 0:
                            logging.debug("Authenticating against db: %s." % (wsm_msg_payloads_mongodb_db_name))
                            wsm_msg_payloads_mongodb_client[wsm_msg_payloads_mongodb_db_name].authenticate(wsm_msg_payloads_mongodb_user, wsm_msg_payloads_mongodb_password,  source=MONGODB_AUTH_DB);
                            logging.debug("Authenticated against db: %s. OK" % (wsm_msg_payloads_mongodb_db_name))

                    for domain in wsm_domain_list:

#                         ws_op_dict = get_ws_operations_status(soma_session, device_host, domain, soma_port, soma_user, soma_user_password)
#                         logging.debug("WS Op dict for domain %s is %s" % (domain, ws_op_dict))
                        thread_id = str(uuid.uuid4())
                        pid_fle = open("/tmp/%s_wsm_%s_wsm_pull.pid" % (input_name.replace("://", "-"), domain), "w")
                        pid_fle.write(thread_id)
                        pid_fle.close()

                        #with WSMPushServerThread(thread_id, domain, input_name, splunk_host, device_name, device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port, use_wsm_transaction_time, wsm_push_max_elements, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb, [domain]) as wsm_push_t:
                        wsm_pull_threads.append(WSMPullPollerThread(thread_id, input_name, splunk_host, device_name, device_host, domain, soma_port, soma_user, soma_user_password, use_wsm, wsm_pull_interval, use_wsm_transaction_time, wsm_pull_max_soap_env_size, wsm_pull_max_elements, wsm_pull_use_custom_formatter, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb, wsm_msg_payloads_mongodb_db_name, wsm_msg_payloads_mongodb_client, ws_op_dict))
                        wsm_pull_threads[-1].start()

    except Exception, ex:
        logging.error("Unhandled Exception occurred in doRun. Exception:" + str(ex))

class SOMAPollerThread(threading.Thread):

    get_status_req = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
        <env:Body>
            <dp:request domain="{domain}" xmlns:dp="http://www.datapower.com/schemas/management">
                <dp:get-status class="{status_class}"/>
            </dp:request>
        </env:Body>
    </env:Envelope>
    """

    def __init__(self, thread_id, input_name, splunk_host, device_name,
                 device_host, soma_port, soma_user, soma_user_password, dpinput_interval,
                 cpu_usage_int, conns_accepted_int, memory_int,
                 network_stats_interface_list, tx_rx_kbps_thruput_int, network_int, system_usage_int, object_status, object_status_int,
                 http_status, http_int, service_memory_status, sql_status, sql_int, mq_status, mq_int,
                 sensors_status, sensors_int, xslt_status, xslt_int, ws_op_status, ws_op_int,
                 web_app_fw_stats, web_app_fw_int, use_wsm, wsm_stats_int, ws_op_dict, domain_list, **kw):

        threading.Thread.__init__(self)

        #logging.debug("Started SOMA Polling Thread %s for input %s." % (thread_id, input_name))

        self.setName(thread_id)
        self.thread_id = thread_id
        self.input_name = input_name
        self.splunk_host = splunk_host
        self.device_name = device_name
        self.device_host = device_host
        self.soma_port = soma_port
        self.soma_user = soma_user
        self.soma_user_password = soma_user_password
        self.dpinput_interval = dpinput_interval
        self.cpu_usage_int = cpu_usage_int
        self.conns_accepted_int = conns_accepted_int
        self.memory_int = memory_int
        self.network_stats_interface_list = network_stats_interface_list
        self.tx_rx_kbps_thruput_int = tx_rx_kbps_thruput_int
        self.network_int = network_int
        self.system_usage_int = system_usage_int

        self.object_status = object_status
        self.object_status_int = object_status_int

        self.http_status = http_status
        self.http_int = http_int

        self.service_memory_status = service_memory_status
        self.sql_status = sql_status
        self.sql_int = sql_int
        self.mq_status = mq_status
        self.mq_int = mq_int
        self.sensors_status = sensors_status
        self.sensors_int = sensors_int
        self.xslt_status = xslt_status
        self.xslt_int = xslt_int
        self.ws_op_status = ws_op_status
        self.ws_op_int = ws_op_int
        self.web_app_fw_stats = web_app_fw_stats
        self.web_app_fw_int = web_app_fw_int
        self.use_wsm = use_wsm
        self.wsm_stats_int = wsm_stats_int
        self.ws_op_dict = ws_op_dict
        self.domain_list = domain_list
        self.kw = kw

        self.soma_url = "https://{device_host}:{soma_port}/service/mgmt/3.0".format(device_host=device_host, soma_port=soma_port)
        self.check_interval_dict = {}

    def log_event(self, event_text):

        index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"
        splunk_event = index_time + " " + event_text
        self.print_xml_single_instance_mode(self.device_name, splunk_event)
        #logging.debug("Logged event: " + splunk_event)

    def print_xml_single_instance_mode(self, host, event):
        #logging.debug("Logging event data: %s" % ("<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)))
        print "<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)

    def run(self):

        while True:
            try:

                file_pid = str(open("/tmp/%s_current.pid" % self.input_name.replace("://", "-"), "r").read())
                #logging.debug("******** this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                if self.getName().strip() != file_pid.strip():
                    #logging.debug("$$$$ Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                    done = True
                    sys.exit(1)
                else:
                    pass

                self.session = requests.Session()
                self.session.auth = (self.soma_user, self.soma_user_password)
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

                self.get_status("default", "ActiveUsers", check_interval=900)
                self.get_status("default", "DateTimeStatus", field_prefix="dp_", check_interval=900)
                self.get_status("default", "DomainStatus", check_interval=900)
                self.get_status("default", "LogTargetStatus", check_interval=900)


                self.get_status("default", "FilesystemStatus", check_interval=self.memory_int)

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
                    self.get_status(domain, "LoadBalancerStatus2", include_domain=True, check_interval=300)

                    if self.object_status:
                        self.get_status(domain, "ObjectStatus", include_domain=True, check_interval=self.object_status_int)

                    if self.http_status:
                        self.get_status(domain, "HTTPConnections", include_domain=True, check_interval=self.http_int)
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

                    if self.use_wsm:
                        self.get_status(domain, "WSMAgentStatus", include_domain=True, check_interval=self.wsm_stats_int)
                        self.get_status(domain, "WSMAgentSpoolers", include_domain=True, check_interval=self.wsm_stats_int)

                    if self.web_app_fw_stats:
                        self.get_status(domain, "WebAppFwAccepted", include_domain=True, check_interval=self.web_app_fw_int)
                        self.get_status(domain, "WebAppFwRejected", include_domain=True, check_interval=self.web_app_fw_int)

                logging.info("SOMA Poller finished in %s seconds." % (time.time() - self.last_run_time))
                #self.session.close()
                    #logging.debug("!!! NOT Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
            except Exception, ex:
                logging.error("Exception occurred in SOMAPoller. Stopping.  Exception: " + str(ex))
                sys.exit(1)
            finally:
                pass
                self.session.close()

            time.sleep(float(self.dpinput_interval))

    def do_soma_request(self, req_data):

        try:
            #r = self.session.post(self.soma_url, data=req_data, auth=(self.soma_user, self.soma_user_password), verify=False)
            r = self.session.post(self.soma_url, data=req_data)
            if r.status_code != 200:
                logging.error("Soma request failed! Status code: %i" % r.status_code)
                return None
            else:
                return r.content

        except Exception, ex:
            logging.error("Exception occurred while making SOMA request. Exception: %s" % (str(ex)))
            return None

    def get_active_users_count(self):

        actve_users_req = self.get_status_req.format(domain="default", status_class="ActiveUsers")

        resp = self.do_soma_request(actve_users_req)

        if resp is None:
            logging.error("Get of active users for device %s failed!" % (self.device_name))
            return

        try:
            doc = lxml.etree.fromstring(resp)
            nl = doc.xpath("//ActiveUsers")

            num_users = len(nl)
            event_text = 'device={dp_name} dp_log_type={log_type} '.format(dp_name=self.device_name, log_type="get_status")
            event_text = event_text + "status_class=active_users_count active_users={}".format(num_users)

            self.log_event(event_text)

        except Exception, ex:
            logging.error("Exception occurred while getting active users for device %s.  Exception: %s" % (self.device_name, str(ex)))

        return

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
                if domain_wsm_op_dict.has_key(domain):
                    if domain_wsm_op_dict[domain].has_key((tran_req_url_port, tran_req_url_uri.strip())):
                        service_obj = domain_wsm_op_dict[domain][(tran_req_url_port, tran_req_url_uri.strip())]

        return service_obj

    def get_status(self, domain, status_class, include_domain=False, field_prefix=None, check_interval=None):

        if check_interval is not None:
            if self.check_interval_dict.has_key((self.device_name, domain, status_class)):
                if (self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)])  < check_interval:
                    #logging.debug("Check interval of %i NOT reached(%s). Not Getting %s for device %s and domain %s." % (check_interval, self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)], status_class, self.device_name, domain))
                    return
                else:
                    #logging.debug("Check interval for %s of %i for device %s and domain %s reached(%s). Getting" % (status_class, check_interval, self.device_name, domain, self.last_run_time - self.check_interval_dict[(self.device_name, domain, status_class)]))
                    self.check_interval_dict[(self.device_name, domain, status_class)] = self.last_run_time
            else:
                self.check_interval_dict[(self.device_name, domain, status_class)] = self.last_run_time

        req = self.get_status_req.format(domain=domain, status_class=status_class)

        resp = self.do_soma_request(req)

        if resp is None:
            logging.error("Error getting %s for device %s." % (status_class, self.device_name))
            return

        need_quotes_re = re.compile(r"[^a-zA-Z0-9_\.]+")
        try:
            doc = lxml.etree.fromstring(resp)
            nl = doc.xpath("//%s" % status_class)

            if len(nl) > 0:
                for dn in nl:
                    
                    if status_class == "ObjectStatus":
                        logging.debug("In ObjectSTatus");

                        object_class_el = dn.xpath("./Class")
                        if object_class_el is not None:
                            if len(object_class_el) == 0:
                                logging.error("Error!  Expected 'Class' element for ObjectStatus")
                                continue
                            else:
                                object_class = object_class_el[0].text
                                logging.debug("In ObjectSTatus object class is: <"+ object_class + ">");
                                if object_class.count("MultiProtocolGateway") > 0:
                                   logging.debug("MPG count ok??")
                                else:
                                   logging.debug("MPG count not ok??")

                                found = False
                                if object_class.count("MultiProtocolGateway") > 0:
                                    found = True
                                if object_class.count("XMLFirewallService") >  0: 
                                    found = True
                                if object_class.count("WebAppFW") >  0: 
                                    found = True
                                if object_class.count("WSGateway") >   0:  
                                    found = True
                                if object_class.count("SSL") >  0: 
                                    found = True
                                if object_class.count("Crypto") >  0: 
                                    found = True
                                if object_class.count("SourceProtocolHandler") > 0:     
                                    found = True
                                
                                if not found:
	                            logging.debug("class " + object_class + " NOT in list!")
                                    continue
                                else:
	                            logging.debug("class " + object_class + " IN list! Yippee!")
                                
                        else:
                            logging.error("Error!  Expected 'Class' element for ObjectStatus")
                            
                    if status_class in ["EthernetInterfaceStatus", "EthernetCountersStatus",  "NetworkTransmitPacketThroughput", "NetworkTransmitDataThroughput", "NetworkReceivePacketThroughput", "NetworkReceiveDataThroughput"]:
                        if self.network_stats_interface_list is not None:
                            if len(self.network_stats_interface_list) > 0:
                                int_name = dn.find("Name")
                                if int_name is None:
                                    int_name = dn.find("InterfaceName")

                                if int_name is not None:
                                    if int_name.text is not None:
                                        if int_name.text.strip() not in self.network_stats_interface_list:
                                            continue

                    event_text = 'device={dp_name} dp_log_type={log_type} '.format(dp_name=self.device_name, log_type="get_status")
                    if include_domain:
                        event_text = event_text + 'domain=%s status_class=%s ' % (domain, status_class)
                    else:
                        event_text = event_text + 'status_class=%s ' % (status_class)



                    if status_class == "WSOperationMetrics":
                        service_endpoint = dn.find("ServiceEndpoint")
                        if service_endpoint is not None:
                            service = self.get_service_from_url(service_endpoint.text, domain)

                            if service is not None:
                                event_text = event_text + 'service="%s" ' % (service)

                    net_int = None
                    for n in dn:
                        tag = n.tag

                        if tag == "Domain":
                            tag = "domain"

                        if field_prefix is not None:
                            tag = field_prefix + tag
                        if n.text is None:
                            event_text = event_text + '%s=%s ' % (tag, '')
                        else:
                            n_text = n.text.strip()
                            need_quotes_m = need_quotes_re.search(n_text)
                            if need_quotes_m is not None:
                                event_text = event_text + '%s="%s" ' % (tag, n_text)
                            else:
                                event_text = event_text + '%s=%s ' % (tag, n_text)

                    self.log_event(event_text)

            else:
                pass
                #logging.debug("No %s results on device %s and domain %s." % (status_class, self.device_name, domain))

        except Exception, ex:
            logging.error("Exception occurred while %s for device %s and domain %s.  Exception: %s" % (status_class, self.device_name, domain, str(ex)))

        return

class WSMPullPollerThread(threading.Thread):


    def __init__(self, thread_id, input_name, splunk_host, device_name,
                 device_host, domain, soma_port, soma_user, soma_user_password, use_wsm, wsm_pull_interval,
                 use_wsm_transaction_time, wsm_pull_max_soap_env_size, wsm_pull_max_elements,wsm_pull_use_custom_formatter,
                 wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb,
                 wsm_msg_payloads_mongodb_db_name, wsm_msg_payloads_mongodb_client, ws_op_dict, **kw):

        threading.Thread.__init__(self)

        #logging.debug("Started WS-M Pull Polling Thread %s for input %s." % (thread_id, input_name))

        self.setName(thread_id)
        self.thread_id = thread_id
        self.input_name = input_name
        self.splunk_host = splunk_host
        self.device_name = device_name
        self.device_host = device_host
        self.domain = domain
        self.soma_port = soma_port
        self.soma_user = soma_user
        self.soma_user_password = soma_user_password
        self.use_wsm = use_wsm
        self.wsm_pull_interval = wsm_pull_interval
        self.use_wsm_transaction_time = use_wsm_transaction_time
        self.wsm_pull_max_soap_env_size = wsm_pull_max_soap_env_size
        self.wsm_pull_max_elements = wsm_pull_max_elements
        self.wsm_pull_use_custom_formatter = wsm_pull_use_custom_formatter
        self.wsm_msg_payloads_to_disk = wsm_msg_payloads_to_disk
        self.wsm_msg_payloads_folder = wsm_msg_payloads_folder
        self.wsm_msg_payloads_use_mongodb = wsm_msg_payloads_use_mongodb
        self.wsm_msg_payloads_mongodb_client = wsm_msg_payloads_mongodb_client
        self.wsm_msg_payloads_mongodb_db = self.wsm_msg_payloads_mongodb_client[wsm_msg_payloads_mongodb_db_name]
        self.wsm_msg_payloads_mongodb_db_name = wsm_msg_payloads_mongodb_db_name
        self.ws_op_dict = ws_op_dict
#         self.wsm_msg_payloads_mongodb_host = wsm_msg_payloads_mongodb_host
#         self.wsm_msg_payloads_mongodb_port = wsm_msg_payloads_mongodb_port
#         self.wsm_msg_payloads_mongodb_user = wsm_msg_payloads_mongodb_user
#         self.wsm_msg_payloads_mongodb_password = wsm_msg_payloads_mongodb_password


        #self.domain_list = domain_list
        #self.subscribed = False
        self.kw = kw

        self.soma_url = "https://{device_host}:{soma_port}/service/mgmt/3.0".format(device_host=device_host, soma_port=soma_port)

        self.session = requests.Session()
        self.session.auth = (self.soma_user, self.soma_user_password)
        self.session.verify = False
        self.enumeration_context = None
        self.current_date = None


    wsm_pull_subscription_req = """<env:Envelope xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:env="http://www.w3.org/2003/05/soap-envelope">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Subscribe</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">{wsm_pull_max_soap_env_size}</wsman:MaxEnvelopeSize>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsman:SelectorSet>
         <wsman:Selector Name="domain">{domain}</wsman:Selector>
      </wsman:SelectorSet>
   </env:Header>
   <env:Body>
      <wse:Subscribe>
         <wse:Delivery Mode="http://schemas.xmlsoap.org/ws/2005/02/management/Pull"/>
         <wse:Expires>{expires}</wse:Expires>
      </wse:Subscribe>
   </env:Body>
</env:Envelope>
"""
    def subscribe_pull(self, domain, expires="PT15M"):
        """

        """
        soma_wsm_pull_subscription_req  = self.wsm_pull_subscription_req.format(domain=domain, expires=expires, wsm_pull_max_soap_env_size=self.wsm_pull_max_soap_env_size, msg_id=uuid.uuid4())

        try:
            r = self.session.post(self.soma_url, data=soma_wsm_pull_subscription_req)

            if r.status_code != 200:
                logging.error("Error while doing pull subscription.  Status_Code: %s" % str(r.status_code))
            else:
                doc = lxml.etree.fromstring(r.content)

                nss = {"wsen": "http://schemas.xmlsoap.org/ws/2004/09/enumeration"}

                nl = doc.xpath("//wsen:EnumerationContext", namespaces=nss)
                if len(nl) > 0:
                    self.enumeration_context = nl[0].text
                    self.subscribed = True
                    return True
                else:
                    logging.error("Error while doing pull subscription.  No EnumerationContext?? Response: %s" % str(r.content))

        except Exception, ex:
            logging.error("Exception while doing pull subscription.  Exception: %s" % str(ex))

        self.subscribed = False
        return False

    wsm_renew_pull_subscription = """<env:Envelope xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:env="http://www.w3.org/2003/05/soap-envelope">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>{enumeration_context}</wse:Identifier>
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Renew</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">{wsm_pull_max_soap_env_size}</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wse:Renew>
         <wsen:Expires>{expires}</wsen:Expires>
      </wse:Renew>
   </env:Body>
</env:Envelope>
"""

    def renew_pull_subscription(self, domain, enumeration_context, expires="PT15M"):
        """

        """

        rc = 8
        soma_wsm_renew_subscription_req  = self.wsm_renew_pull_subscription.format(domain=domain, expires=expires, wsm_pull_max_soap_env_size=self.wsm_pull_max_soap_env_size, msg_id=uuid.uuid4(), enumeration_context=enumeration_context)

        try:
            r = self.session.post(self.soma_url, data=soma_wsm_renew_subscription_req)

            if r.status_code != 200:
                logging.error("Error while renewing push subscription.  Status_Code: %s" % str(r.status_code))
                rc = 8
                self.subscribed = False
            else:
                doc = lxml.etree.fromstring(r.content)

                nss = {"wsen": "http://schemas.xmlsoap.org/ws/2004/09/enumeration", "wse": "http://schemas.xmlsoap.org/ws/2004/08/eventing"}

                nl = doc.xpath("//wse:RenewResponse", namespaces=nss)
                if len(nl) > 0:
                    logging.debug("Renew of %s OK." % str(enumeration_context))
                    rc = 0
                    self.subscribed = True
                else:
                    self.subscribed = False
                    if r.content.count("UnableToRenew") > 0 or r.content.count("DestinationUnreachable") > 0:
                        rc = 4
                    else:
                        logging.error("Error while doing pull renew.  Response: %s" % str(r.content))

        except Exception, ex:
            logging.error("Exception while doing renew subscription.  Exception: %s" % str(ex))
            rc = 8
            self.subscribed = False

        return rc


    wsm_pull_unsubscribe_req = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>{enumeration_context}</wse:Identifier>
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Unsubscribe</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">51200</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wse:Unsubscribe>
         <wsen:EnumerationContext>{enumeration_context}</wsen:EnumerationContext>
      </wse:Unsubscribe>
   </env:Body>
</env:Envelope>
"""

    def unsubscribe_pull(self, expires="PT15M"):
        """

        """
        rc = False
        try:
            soma_wsm_unsub_pull_req  = self.wsm_pull_unsubscribe_req.format(domain=self.domain, msg_id=uuid.uuid4(), enumeration_context=self.enumeration_context)

            r = self.session.post(self.soma_url, data=soma_wsm_unsub_pull_req)

            if r.status_code != 200:
                logging.error("Error while unsubscribing push subscription.  Status_Code: %s" % str(r.status_code))

            else:
                rc = True
                if r.content.count(":Body") > 0:
                    logging.debug("Unsubscribed pull.")

                else:
                    logging.error("HTTP 200 but no soap body?")

        except Exception, ex:
            logging.error("Exception while doing pull unsubscription.  Exception: %s" % str(ex))

        return rc



    def log_event(self, event_text, wsm_tran_time=None):

        index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"
        #logging.debug("Log event - self.use_wsm_transaction_time: " + str(self.use_wsm_transaction_time))
        #logging.debug("Log event - wsm_tran_time: " + str(wsm_tran_time))

        if self.use_wsm_transaction_time > 0 and wsm_tran_time is not None:
            #logging.debug("Using wsm tran time of: " + str(wsm_tran_time))
            try:
                wsm_index_time = "[" +  datetime.datetime.fromtimestamp(wsm_tran_time).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"
                index_time = wsm_index_time
                #logging.error("index time is: " + index_time)
            except Exception, ex:
                logging.error("HUH?  Could not parse wsm-tran time.  Exception:" + str(ex))
                pass

        splunk_event = index_time + " " + event_text
        self.print_xml_single_instance_mode(self.device_name, splunk_event)
        #logging.debug("Logged event: %s " % splunk_event)

    def print_xml_single_instance_mode(self, host, event):
        print "<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)

    def run(self):

        sub_time = 0
        renew_time = 300

        while True:
            try:

                file_pid = str(open("/tmp/%s_wsm_%s_wsm_pull.pid" % (self.input_name.replace("://", "-"), self.domain), "r").read())
                #logging.debug("~~~ WSM Pull Thread this pid:" + str(self.getName()) + " File pid:" + str(file_pid))

                if self.getName().strip() != file_pid.strip():
                    #logging.debug("~~~ WSM Pull Thread Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                    try:
                        if not self.unsubscribe_pull():
                            #logging.error("Unsubscribe failed?")
                            pass
                        else:
                            #logging.debug("Unsubscribe OK?")
                            pass
                    except Exception, ex:
                        pass

                    done = True
                    sys.exit(1)
                else:
                    pass

                if ((time.time() -  sub_time) > renew_time) or (sub_time == 0):
                    #logging.debug("WSM Pull Sub Timeout")
                    if sub_time == 0:
                        sub_time = time.time()
                        if not self.subscribe_pull(self.domain):
                            logging.error("Pull Subscription failed?  Will try again on timeout.")
                        else:
                            logging.debug("Pull Subscription OK. Context: %s " % (self.enumeration_context))
                    else:
                        sub_time = time.time()
                        rc = self.renew_pull_subscription(self.domain, self.enumeration_context)
                        if rc == 0:
                            logging.debug("Pull subscription renew ok")
                        else:
                            if rc == 4:
                                logging.info("Renew failed! No Subscription?  Subscribing...")
                                if not self.subscribe_pull(self.domain):
                                     logging.error("Pull Subscription on renew failed?  Will try again on timeout. Context: %s " % (self.enumeration_context))
                                else:
                                    logging.debug("Pull Subscription on renew OK. Context: %s " % (self.enumeration_context))
                            else:
                                if rc == 8:
                                    logging.error("Renew failed!")

                if self.current_date !=  datetime.datetime.now().strftime("%Y%m%d"):
                    #logging.debug("SM Pull in run() - Date changed. Starting new db.")
                    #first = False
                    #if self.current_date is None:
                    #    first = True

                    self.current_date =  datetime.datetime.now().strftime("%Y%m%d")

                    if self.wsm_msg_payloads_use_mongodb:
                        #logging.debug("WSM pull in run() - Date changed. Starting new collection: %s.%s" % (self.domain, self.current_date))

                        self.current_collection = "%s.%s" % (self.current_date, self.domain)
                        # create index on starttimeutc
                        self.wsm_msg_payloads_mongodb_db[self.current_collection].create_index("starttimeutc")
                        #logging.debug("WSM pull in run() - Date changed. DB changed OK.")

                    if self.wsm_msg_payloads_to_disk:
                        try:
                            self.current_folder = os.path.join(self.wsm_msg_payloads_folder, self.current_date)
                            os.makedirs(os.path.join(self.current_folder, self.domain))

                        except Exception, ex:
                            logging.error("Exception occurred while create new folder. Exception: %s" % str(ex))


                if self.subscribed == True:
                    while self.pull_request():
                        #logging.debug("PUll request Ok.")
                        time.sleep(0.01)

                    #logging.debug("PUll request failed.")


            except Exception, ex:
                logging.error("Exception in WS-M pull thread.  Exception: %s" % (str(ex)))

            time.sleep(self.wsm_pull_interval)

    wsm_pull_req = """<env:Envelope xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:env="http://www.w3.org/2003/05/soap-envelope">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>{enumeration_context}</wse:Identifier>
         {wsm_pull_use_custom_formatter}
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/enumeration/Pull</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">{wsm_pull_max_soap_env_size}</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wsen:Pull>
         <wsen:EnumerationContext>{enumeration_context}</wsen:EnumerationContext>
         <wsen:MaxElements>{wsm_pull_max_elements}</wsen:MaxElements>
      </wsen:Pull>
   </env:Body>
</env:Envelope>
"""

    def pull_request(self):

        soma_wsm_pull_req  = ""
        if self.wsm_pull_use_custom_formatter > 0:
            wsm_custom_formatter_element_text = '<dpt:Format xmlns:dpt="http://www.datapower.com/schemas/transactions">splunk_wsm</dpt:Format>'
            soma_wsm_pull_req  = self.wsm_pull_req.format(domain=self.domain, msg_id=uuid.uuid4(), enumeration_context=self.enumeration_context, wsm_pull_max_soap_env_size=self.wsm_pull_max_soap_env_size, wsm_pull_max_elements=self.wsm_pull_max_elements, wsm_pull_use_custom_formatter=wsm_custom_formatter_element_text)
        else:
            soma_wsm_pull_req  = self.wsm_pull_req.format(domain=self.domain, msg_id=uuid.uuid4(), enumeration_context=self.enumeration_context, wsm_pull_max_soap_env_size=self.wsm_pull_max_soap_env_size, wsm_pull_max_elements=self.wsm_pull_max_elements, wsm_pull_use_custom_formatter="")


        try:
            r = self.session.post(self.soma_url, data=soma_wsm_pull_req)

            if r.status_code != 200:
                logging.error("Error while doing push request.  Status_Code: %s Response: %s" % (str(r.status_code), r.content))
            else:
                if r.content.count("PullResponse"):
                    if self.wsm_pull_use_custom_formatter > 0:
                        self.process_wsm_formatted_events(r.content)
                    else:
                        self.process_wsm_events(r.content)
                    #logging.debug("Pulled data ok.")
                    return True
                else:
                    if r.content.count("TimedOut") > 0:
                        #logging.debug("No data to pull.")
                        pass
                    else:
                        logging.error("No PullResponse?" + r.content)


        except Exception, ex:
            logging.error("Exception while doing pull subscription.  Exception: %s" % str(ex))

        return False

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
                if domain_wsm_op_dict.has_key(domain):
                    if domain_wsm_op_dict[domain].has_key((tran_req_url_port, tran_req_url_uri.strip())):
                        service_obj = domain_wsm_op_dict[domain][(tran_req_url_port, tran_req_url_uri.strip())]

        return service_obj


    def process_wsm_formatted_events(self, event_message):

        #logging.debug("Got event_message:" + str(event_message))
        try:
            db_obj = {"device": self.device_name, "domain": self.domain}

            tran_start_tag = "transaction_id"
            tran_end_tag = "</transaction>"
            all_done = False
            current_pos = 0
            while not all_done:
                current_pos = event_message.find(tran_start_tag, current_pos)
                if current_pos > 0:
                    end_pos = event_message.find(tran_end_tag, current_pos)

                    if end_pos > 0:
                        tran_text = event_message[current_pos:end_pos]
                        #logging.debug("tran text:" + str(tran_text))

                        tran_id = None
                        s_pos = tran_text.find("transaction_id=")
                        if s_pos >= 0:
                            #logging.debug("tran id found?")
                            e_pos = tran_text.find(" ", s_pos + 1)

                            if e_pos > 0:
                                #logging.debug("tran id space found")
                                tran_id = tran_text[s_pos + 15:e_pos]
                            else:
                                pass
                                #logging.debug("tran id epos not > 0")

                        #logging.debug("tran_id:" + str(tran_id))
                        request_url = None
                        s_pos = tran_text.find("request_url=")
                        if s_pos > 0:
                            e_pos = tran_text.find(" ", s_pos)

                            if e_pos > 0:
                                request_url = tran_text[s_pos + 12:e_pos].replace('"', "")

                        #logging.debug("request_url:" + str(request_url))

                        ws_operation = None
                        ws_operation_s_pos = tran_text.find('ws_operation="')
                        if ws_operation_s_pos > 0:
                            ws_operation_e_pos = tran_text.find('"', ws_operation_s_pos + 14)

                            if ws_operation_e_pos > 0:
                                ws_operation = tran_text[ws_operation_s_pos + 14:ws_operation_e_pos].replace('"', "")
                                new_ws_operation = ws_operation
                                if ws_operation.count("}"):
                                    new_ws_operation = ws_operation[ws_operation.find("}") + 1:]
                                    tran_text = tran_text[:ws_operation_s_pos + 14] + new_ws_operation + tran_text[ws_operation_e_pos:]

                        #logging.debug("ws_operation:" + str(ws_operation))


                        web_service = None
                        web_service_s_pos = tran_text.find('webservice="')
                        if web_service_s_pos > 0:
                            web_service_e_pos = tran_text.find('"', web_service_s_pos + 12)

                            if web_service_e_pos > 0:
                                web_service = tran_text[web_service_s_pos + 12:web_service_e_pos].replace('"', "")
                                #logging.debug("web_service:" + web_service)
                                if web_service.count("}"):
                                    web_service = web_service[web_service.find("}") + 1:]
                                    tran_text = tran_text[:web_service_s_pos + 12] + web_service + tran_text[web_service_e_pos:]



                        service_port = None
                        service_port_s_pos = tran_text.find('service_port="')
                        if service_port_s_pos > 0:
                            service_port_e_pos = tran_text.find('"', service_port_s_pos + 14)

                            if service_port_e_pos > 0:
                                service_port = tran_text[service_port_s_pos + 14:service_port_e_pos].replace('"', "")
                                if service_port.count("}"):
                                    service_port = service_port[service_port.find("}") + 1:]
                                    tran_text = tran_text[:service_port_s_pos + 14] + service_port + tran_text[service_port_e_pos:]

                        #logging.debug("service_port:" + str(service_port))

                        service_obj = "Unknown"
                        if ws_operation is not None:
                            if ws_operation.count("{defaultns.datapower.com}") > 0:
                                service_obj = ws_operation.replace("{defaultns.datapower.com}", "")

                            else:
                                service_obj = self.get_service_from_url(request_url, self.domain)

                            s_pos = ws_operation.find("}")
                            if s_pos > 0:
                                ws_operation = ws_operation[s_pos + 1:]
                        else:
                            logger.error("Expected ws_operation field but not found? Will try to get service anyway.")
                            service_obj = self.get_service_from_url(request_url, self.domain)
                            if service_obj is None:
                                service_obj = "Unknown"


                        #logging.debug("service_obj:" + str(service_obj))

                        start_time_utc = None
                        s_pos = tran_text.find("start_time_utc=")
                        if s_pos > 0:
                            e_pos = tran_text.find(" ", s_pos)

                            if e_pos > 0:
                                start_time_utc = tran_text[s_pos + 15:e_pos].replace('"', "")

                        #logging.debug("start_time_utc:" + str(start_time_utc))

                        start_time = None
                        s_pos = tran_text.find('start_time="')
                        if s_pos > 0:
                            e_pos = tran_text.find('"', s_pos + 12)

                            if e_pos > 0:
                                start_time = tran_text[s_pos + 12:e_pos].replace('"', "")

                        #logging.debug("start_time:" + str(start_time))

                        tran_status = None
                        s_pos = tran_text.find("status=ok")
                        if s_pos > 0:
                            tran_status = "ok"
                        else:
                            s_pos = tran_text.find("status=fail")
                            if s_pos > 0:
                                tran_status = "fail"
                            else:
                                logging.error("No status value found!!")
#                                logging.error("tran_text:" + tran_text)
#
#                             e_pos = tran_text.find(" ", s_pos)
#                             logging.error("tran_status e_pos:" + str(e_pos))
#                             if e_pos > 0:
#                                 tran_status = tran_text[s_pos + 7:e_pos].replace('"', "")

                        #logging.error("tran_status:" + str(tran_status))

                        try:
                            db_obj["starttimeutc"] = int(start_time_utc)
                        except:
                            db_obj["starttimeutc"] = str(start_time_utc)

                        db_obj["tranid"] = tran_id
                        db_obj["service"] = service_obj
                        db_obj["operation"] = ws_operation
                        db_obj["status"] = tran_status

                        request_message = None
                        request_message_s_pos = tran_text.find("request_message=")
                        request_message_e_pos = 0
                        request_message_id = None
                        if request_message_s_pos > 0:
                            request_message_e_pos = tran_text.find(" ", request_message_s_pos)

                            if request_message_e_pos > 0:
                                request_message = tran_text[request_message_s_pos + 16:request_message_e_pos].replace('"', "")
                                #logging.debug("request_message:" + str(request_message))
                                ins_id = None
                                try:
                                    if self.wsm_msg_payloads_use_mongodb > 0:
                                        new_db_obj = db_obj.copy()
                                        new_db_obj["payload_type"] = "request"
                                        new_db_obj["payload"] = request_message.replace("\n", "")
                                        #new_db_obj_lst.append(new_db_obj)

                                        ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                        ins_id = str(ins_id)
                                        #logging.debug("Tid: %s request_message Inserted: %s " %(tid, ins_id))

                                    if self.wsm_msg_payloads_to_disk > 0:
                                        if self.ins_id is None:
                                            ins_id = uuid.uuid4()

                                        msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tran_id, ins_id)), "wb")
                                        msg_file.write(request_message)
                                        msg_file.close()
                                except Exception, ex:
                                    logger.error("Exception occured while writing request message.  Exception:" + str(ex))
                                request_message_id = ins_id
                                #logging.debug("request_message_id:" + str(request_message_id))

                            else:
                                logging.error("Found be request message start but no end?")


                        response_message = None
                        response_message_id = None
                        response_message_s_pos = tran_text.find("response_message=")
                        response_message_e_pos = 0
                        if response_message_s_pos > 0:
                            response_message_e_pos = tran_text.find(" ", response_message_s_pos)

                            if response_message_e_pos > 0:
                                response_message = tran_text[response_message_s_pos + 17:response_message_e_pos].replace('"', "")
                                #logging.debug("response_message:" + str(response_message))
                                ins_id = None
                                try:
                                    if self.wsm_msg_payloads_use_mongodb > 0:
                                        new_db_obj = db_obj.copy()
                                        new_db_obj["payload_type"] = "response"
                                        new_db_obj["payload"] = response_message.replace("\n", "")
                                        #new_db_obj_lst.append(new_db_obj)

                                        ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                        ins_id = str(ins_id)
                                        #logging.debug("Tid: %s request_message Inserted: %s " %(tid, ins_id))

                                    if self.wsm_msg_payloads_to_disk > 0:
                                        if self.ins_id is None:
                                            ins_id = uuid.uuid4()

                                        msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tran_id, ins_id)), "wb")
                                        msg_file.write(response_message)
                                        msg_file.close()
                                except Exception, ex:
                                    logger.error("Exception occured while writing response message.  Exception:" + str(ex))
                                response_message_id = ins_id
                                #logging.debug("response_message_id:" + str(response_message_id))
                            else:
                                logging.error("Found request message start bu no end?")


                        be_request_message = None
                        be_request_message_id = None
                        be_request_message_s_pos = tran_text.find("be_request_message=")
                        be_request_message_e_pos = 0
                        if be_request_message_s_pos > 0:
                            be_request_message_e_pos = tran_text.find(" ", be_request_message_s_pos)
                            #logging.debug("be_request_message_e_pos:" + str(be_request_message_e_pos))
                            if be_request_message_e_pos > 0:
                                be_request_message = tran_text[be_request_message_s_pos + 19:be_request_message_e_pos].replace('"', "")

                                ins_id = None
                                try:
                                    if self.wsm_msg_payloads_use_mongodb > 0:
                                        new_db_obj = db_obj.copy()
                                        new_db_obj["payload_type"] = "backend_request"
                                        new_db_obj["payload"] = be_request_message.replace("\n", "")
                                        #new_db_obj_lst.append(new_db_obj)

                                        ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                        ins_id = str(ins_id)
                                        #logging.debug("Tid: %s request_message Inserted: %s " %(tid, ins_id))

                                    if self.wsm_msg_payloads_to_disk > 0:
                                        if self.ins_id is None:
                                            ins_id = uuid.uuid4()

                                        msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tran_id, ins_id)), "wb")
                                        msg_file.write(be_request_message)
                                        msg_file.close()
                                except Exception, ex:
                                    logger.error("Exception occured while writing be_request message.  Exception:" + str(ex))
                                be_request_message_id = ins_id
                                #logging.debug("be_request_message_id:" + str(be_request_message_id))

                            else:
                                logging.error("Found be request message start but no end?")


                        be_response_message = None
                        be_response_message_id = None
                        be_response_message_s_pos = tran_text.find("be_response_message=")
                        be_response_message_e_pos = 0
                        if be_response_message_s_pos > 0:
                            be_response_message_e_pos = tran_text.find(" ", be_response_message_s_pos)

                            if be_response_message_e_pos > 0:
                                be_response_message = tran_text[be_response_message_s_pos + 20:be_response_message_e_pos].replace('"', "")
                                #logging.debug("be_response_message:" + str(be_response_message))
                                ins_id = None
                                try:
                                    if self.wsm_msg_payloads_use_mongodb > 0:
                                        new_db_obj = db_obj.copy()
                                        new_db_obj["payload_type"] = "backend_response"
                                        new_db_obj["payload"] = be_response_message.replace("\n", "")
                                        #new_db_obj_lst.append(new_db_obj)

                                        ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                        ins_id = str(ins_id)
                                        #logging.debug("Tid: %s request_message Inserted: %s " %(tid, ins_id))

                                    if self.wsm_msg_payloads_to_disk > 0:
                                        if self.ins_id is None:
                                            ins_id = uuid.uuid4()

                                        msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tran_id, ins_id)), "wb")
                                        msg_file.write(be_response_message)
                                        msg_file.close()
                                except Exception, ex:
                                    logger.error("Exception occured while writing be_response message.  Exception:" + str(ex))
                                be_response_message_id = ins_id
                                #logging.debug("be_response_message_id:" + str(be_response_message_id))
                            else:
                                logging.error("Found be request message start but no end?")


                        new_tran_text = tran_text
                        if request_message_id is not None:
                            s_pos = new_tran_text.find("request_message=")
                            if s_pos > 0:
                                e_pos = new_tran_text.find(" ", s_pos)
                                if e_pos > 0:
                                    new_tran_text = new_tran_text[:s_pos + 16] + request_message_id + new_tran_text[e_pos:]
                                else:
                                    logging.error("Huh?  request messageinserted but  end not found?")
                            else:
                                logging.error("HuH?  Inserted requests message but no text found?")

                        if response_message_id is not None:
                            s_pos = new_tran_text.find("response_message=")
                            if s_pos > 0:
                                e_pos = new_tran_text.find(" ", s_pos)
                                if e_pos > 0:
                                    new_tran_text = new_tran_text[:s_pos + 17] + response_message_id + new_tran_text[e_pos:]
                                else:
                                    logging.error("Huh?  response messageinserted but  end not found?")
                            else:
                                logging.error("HuH?  Inserted response message but no text found?")

                        if be_request_message_id is not None:
                            s_pos = new_tran_text.find("be_request_message=")
                            if s_pos > 0:
                                e_pos = new_tran_text.find(" ", s_pos)
                                if e_pos > 0:
                                    new_tran_text = new_tran_text[:s_pos + 19] + be_request_message_id + new_tran_text[e_pos:]
                                else:
                                    logging.error("Huh?  be_request_message inserted but  end not found?")
                            else:
                                logging.error("HuH?  Inserted be_request_message message but no text found?")

                        if be_response_message_id is not None:
                            s_pos = new_tran_text.find("be_response_message=")
                            if s_pos > 0:
                                e_pos = new_tran_text.find(" ", s_pos)
                                if e_pos > 0:
                                    new_tran_text = new_tran_text[:s_pos + 20] + be_response_message_id + new_tran_text[e_pos:]
                                else:
                                    logging.error("Huh?  be_response_message_id inserted but  end not found?")
                            else:
                                logging.error("HuH?  Inserted be_response_message but no text found?")

                        #logging.debug("new tran text:" + str(new_tran_text))
                        event_text = 'device={dp_name} dp_log_type={log_type} '.format(dp_name=self.device_name, log_type="wsm_evt")
                        event_text = event_text + 'domain=%s ' % self.domain
                        event_text = event_text + 'service=%s ' % service_obj
                        #event_text = event_text + 'status=%s ' % tran_status

                        if self.wsm_msg_payloads_to_disk:
                            event_text = 'msg_folder="%s" ' % self.current_folder

                        if self.wsm_msg_payloads_use_mongodb and (response_message_id is not None or request_message_id is not None or be_response_message_id is not None or be_request_message_id is not None):
                            #event_text = event_text + 'db_name="%s" ' % self.wsm_msg_payloads_mongodb_db_name
                            event_text = event_text + 'collection=%s ' % self.current_collection

                        ws_tran_time = None
                        event_text = event_text + new_tran_text

                        #logging.debug("event text:" + str(event_text))

                        wsm_tran_time = None
                        #logging.debug("use_wsm_transaction_time:" + str(self.use_wsm_transaction_time))
                        if self.use_wsm_transaction_time > 0:
                            #logging.debug("Setting ws_tran_time to " + str(start_time_utc))
                            try:
                                wsm_tran_time = int(start_time_utc)
                            except:
                                pass

                        self.log_event(event_text, wsm_tran_time=wsm_tran_time)

                        current_pos = end_pos
                    else:
                        logging.error("Found start transaction tag but no end tag?")
                        all_done = True

                else:
                    all_done = True
                    #logging.debug("No mpore transaction tags to process.")

        except Exception, ex:
            logging.error("Exception while processing formatted WSM events. Exception: " + str(ex))


    def process_wsm_events(self, events_msg):

        try:
            #logging.debug("Recieved events:" + events_msg)

            doc = lxml.etree.fromstring(events_msg)

            nss = {"wsman": "http://schemas.xmlsoap.org/ws/2005/02/management", "trans": "http://www.datapower.com/schemas/transactions", "dpg": "http://datapower-modular-input.jjjw420.github.com"}
            domain = self.domain

            nl = doc.xpath("//trans:transaction[@tid]", namespaces=nss)
            if nl is not None:
                for n in nl:

                    start_time_n = n.find("trans:start-time", namespaces=nss)
                    transaction_id_n = n.find("trans:transaction-id", namespaces=nss)
                    tid = ""


                    db_obj = {"device": self.device_name, "domain": domain}
                    if transaction_id_n is not None:
                        db_obj["tranid"] = transaction_id_n.text

                        tid = transaction_id_n.text

                    start_time_utc = None
                    if start_time_n is not None:
                        start_time_utc = start_time_n.attrib["utc"]
                        try:
                            db_obj["starttimeutc"] = int(start_time_utc)
                        except:
                            db_obj["starttimeutc"] = str(start_time_utc)

                    service_obj = "Unknown"
                    operation_obj = "Unknown"
                    tran_status = "ok"

                    if n.find("trans:fault-message", namespaces=nss) is not None or n.find("trans:error-code", namespaces=nss) is not None:
                        tran_status = "fail"

                    ws_op_n = n.find("trans:ws-operation", namespaces=nss)
                    if ws_op_n is not None:
                        if ws_op_n.text is not None:
                            ws_op_n_ns_start = ws_op_n.text.find("}")
                            if ws_op_n_ns_start > 0:
                                operation_obj = ws_op_n.text[ws_op_n_ns_start + 1:]
                            else:
                                operation_obj = ws_op_n.text
                            #logging.debug("Wsoperation text: " + ws_op_n.text)

                            if ws_op_n.text.count("{defaultns.datapower.com}") > 0:
                                #logging.debug("Default dns found?")
                                service_obj = ws_op_n.text.replace("{defaultns.datapower.com}","")
                            else:
                                #logging.debug("Default dns found? Getting request url")
                                tran_req_url_n = n.find("trans:request-url", namespaces=nss)
                                if tran_req_url_n  is not None:
                                    if tran_req_url_n.text is not None:
                                        tran_req_url_port = ""
                                        tran_req_url_uri = ""
                                        first_c = tran_req_url_n.text.find("://")
                                        port_start_pos = tran_req_url_n.text.find(":", first_c + 1)
                                        if port_start_pos > 0:
                                            port_end_pos = tran_req_url_n.text.find("/", port_start_pos)

                                            if port_end_pos > 0:
                                                tran_req_url_port = tran_req_url_n.text[port_start_pos + 1:port_end_pos]
                                                url_parms_start = tran_req_url_n.text.find("?", port_end_pos)
                                                if url_parms_start > 0:
                                                    tran_req_url_uri = tran_req_url_n.text[port_end_pos:url_parms_start]
                                                else:
                                                    tran_req_url_uri = tran_req_url_n.text[port_end_pos:]
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
                                        if tran_req_url_port != "" and tran_req_url_uri != "":
                                            #logging.debug("str(self.ws_op_dict) = " + str(self.ws_op_dict))
                                            if domain_wsm_op_dict.has_key(domain):
                                                if domain_wsm_op_dict[domain].has_key((tran_req_url_port, tran_req_url_uri.strip())):
                                                    service_obj = domain_wsm_op_dict[domain][(tran_req_url_port, tran_req_url_uri.strip())]
                                            else:
                                                logging.debug("Huh?  both uri and port nothoing?")

                                else:
                                    pass
                                    #logging.debug("HUH?  No request url?")

                    db_obj["service"] = service_obj
                    db_obj["operation"] = operation_obj
                    db_obj["status"] = tran_status

                    #logging.debug("service_obj: " + str(service_obj))

                    if self.wsm_msg_payloads_to_disk > 0 or self.wsm_msg_payloads_use_mongodb > 0:

                        new_db_obj_lst = []
                        fs_req_msg = n.find("trans:request-message", namespaces=nss)
                        if fs_req_msg is not None:
                            if len(fs_req_msg) > 0:
                                    try:

                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(fs_req_msg[0]),9))
                                        ins_id = None
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["payload_type"] = "request"
                                            new_db_obj["payload"] = msg_comp.replace("\n", "")
                                            #new_db_obj_lst.append(new_db_obj)

                                            ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                            ins_id = str(ins_id)
                                            #logging.debug("Tid: %s request_message Inserted: %s " %(tid, ins_id))

                                        if self.wsm_msg_payloads_to_disk > 0:
                                            if self.ins_id is None:
                                                ins_id = uuid.uuid4()

                                            msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tid, ins_id)), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        fs_req_msg.remove(fs_req_msg[0])
                                        fs_req_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error("Exception occurred while inserting or writing FS Request message! Ex:" + str(ex))


                        fs_resp_msg = n.find("trans:response-message", namespaces=nss)
                        if fs_resp_msg is not None:
                            if len(fs_resp_msg) > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(fs_resp_msg[0]),9))
                                        ins_id = None
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["payload_type"] = "response"
                                            new_db_obj["payload"] = msg_comp.replace("\n", "")
                                            new_db_obj_lst.append(new_db_obj)

                                            ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                            ins_id = str(ins_id)
                                            #logging.debug("Tid: %s response_message Inserted: %s " %(tid, ins_id))

                                        if self.wsm_msg_payloads_to_disk > 0:
                                            if self.ins_id is None:
                                                ins_id = uuid.uuid4()

                                            msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tid, ins_id)), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        fs_resp_msg.remove(fs_resp_msg[0])
                                        fs_resp_msg.text = ins_id


                                    except Exception, ex:
                                        logging.error( "Exception occurred while inserting or writing FS Response message:" + str(ex))


                        bs_req_msg = n.find("trans:backend-message/trans:request-message", namespaces=nss)
                        if bs_req_msg is not None:
                            if len(bs_req_msg) > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(bs_req_msg[0]),9))
                                        ins_id = None
                                        if self.wsm_msg_payloads_use_mongodb > 0:

                                            new_db_obj = db_obj.copy()
                                            new_db_obj["payload_type"] = "backend_request"
                                            new_db_obj["payload"] = msg_comp.replace("\n", "")
                                            new_db_obj_lst.append(new_db_obj)

                                            ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                            ins_id = str(ins_id)
                                            #logging.debug("Tid: %s be_request_message Inserted: %s " %(tid, ins_id))

                                        if self.wsm_msg_payloads_to_disk > 0:
                                            if self.ins_id is None:
                                                ins_id = uuid.uuid4()

                                            msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tid, ins_id)), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        bs_req_msg.remove(bs_req_msg[0])
                                        bs_req_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error("Exception occurred while inserting or writing BS Request message" + str(ex))


                        bs_resp_msg = n.find("trans:backend-message/trans:response-message", namespaces=nss)
                        if bs_resp_msg is not None:
                            if len(bs_resp_msg) > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(bs_resp_msg[0]),9))
                                        ins_id = None
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["payload_type"] = "backend_response"
                                            new_db_obj["payload"] = msg_comp.replace("\n", "")
                                            #new_db_obj_lst.append(new_db_obj)
                                            ins_id = self.wsm_msg_payloads_mongodb_db[self.current_collection].insert_one(new_db_obj).inserted_id
                                            ins_id = str(ins_id)
                                            #logging.debug("Tid: %s be_response_message Inserted: %s " %(tid, ins_id))

                                        if self.wsm_msg_payloads_to_disk > 0:
                                            if self.ins_id is None:
                                                ins_id = uuid.uuid4()

                                            msg_file = open(os.path.join(self.current_folder, domain, "%s_%s.dat" % (tid, ins_id)), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        bs_resp_msg.remove(bs_resp_msg[0])
                                        bs_resp_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error(" Exception occurred while inserting or writing BS Response message" + str(ex))
                                        pass


                    event_text = 'device={dp_name} dp_log_type={log_type} '.format(dp_name=self.device_name, log_type="wsm_evt")
                    event_text = event_text + 'domain=%s ' % domain
                    event_text = event_text + 'service=%s ' % service_obj
                    event_text = event_text + 'status=%s ' % tran_status

                    if self.wsm_msg_payloads_to_disk:
                        event_text = 'msg_folder="%s" ' % self.current_folder

                    if self.wsm_msg_payloads_use_mongodb:
                        #event_text = event_text + 'db_name="%s" ' % self.wsm_msg_payloads_mongodb_db_name
                        event_text = event_text + 'collection=%s ' % self.current_collection

                    need_quotes_re = re.compile(r"[^a-zA-Z0-9_\.]+")
                    wsm_tran_time = None
                    for el in n:
                        ns_end = el.tag.find("}")
                        el_tag = el.tag
                        if ns_end > 0:
                            el_tag = el.tag[ns_end + 1:]

                        if el_tag == "backend-message":
                            el_tag = "be"

                        el_tag = el_tag.replace("-", "_")
                        if len(el) > 0:
                            for eel in el:
                                eel_tag = eel.tag
                                ns_end = eel.tag.find("}")
                                if ns_end > 0:
                                    eel_tag = eel.tag[ns_end + 1:]

                                eel_tag = eel_tag.replace("-", "_")

                                if eel.text is None:
                                    event_text = event_text + '%s=%s ' % (el_tag + "_" + eel_tag,  "")
                                else:
                                    eel_text = eel.text.replace("\n", "")
                                    eel_text_ns = eel_text.find("}")
                                    if eel_text_ns > 0:
                                        eel_text = eel_text[eel_text_ns + 1:]

                                    need_quotes_m = need_quotes_re.search(eel_text)
                                    if need_quotes_m is not None:
                                        event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag, eel_text)
                                    else:
                                        event_text = event_text + '%s=%s ' % (el_tag + "_" + eel_tag, eel_text)

                                if len(eel.attrib) > 0:
                                    for el_a, el_a_v in eel.attrib.items():
                                        el_a_v = el_a_v.replace("\n", "")
                                        el_a_v_ns = el_a_v.find("}")
                                        if el_a_v_ns > 0:
                                            el_a_v = el_a_v[el_a_v_ns + 1:]

                                        need_quotes_m = need_quotes_re.search(el_a_v)
                                        if need_quotes_m is not None:
                                            event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag + "_" + el_a, el_a_v)
                                        else:
                                            event_text = event_text + '%s=%s ' % (el_tag + "_" + eel_tag + "_" + el_a, el_a_v)

                        else:
                            if el.text is None:
                                event_text = event_text + '%s=%s ' % (el_tag,  "")
                            else:
                                el_text = el.text.replace("\n", "")
                                el_text_ns = el_text.find("}")
                                if el_text_ns > 0:
                                    el_text = el_text[el_text_ns + 1:]

                                need_quotes_m = need_quotes_re.search(el_text)
                                if need_quotes_m is not None:

                                    event_text = event_text +  '%s="%s" ' % (el_tag, el_text)
                                else:
                                    event_text = event_text +  '%s=%s ' % (el_tag, el_text)


                            if len(el.attrib) > 0:
                                for el_a, el_a_v in el.attrib.items():
                                    el_a_v = el_a_v.replace("\n", "")
                                    el_a_v_ns = el_a_v.find("}")
                                    if el_a_v_ns > 0:
                                        el_a_v = el_a_v[el_a_v_ns + 1:]
                                    need_quotes_m = need_quotes_re.search(el_a_v)
                                    if need_quotes_m is not None:
                                        event_text = event_text + '%s="%s" ' % (el_tag + "_" + el_a, el_a_v)
                                    else:
                                        event_text = event_text + '%s=%s ' % (el_tag + "_" + el_a, el_a_v)

                    wsm_tran_time = None
                    if self.use_wsm_transaction_time > 0:
                        wsm_tran_time = start_time_utc

                    self.log_event(event_text, wsm_tran_time=wsm_tran_time)

                return True

        except Exception, ex:
            logging.error("Exception occurred in WSM Pull thread! Exception:" + str(ex))

        return False


class WSMPushServerThread(threading.Thread):

    class WSMPushRestService(object):
        def __init__(self, device_name, domain_sub_list, use_wsm_transaction_time, wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb=True, cdb_db=None):

            self.device_name = device_name
            self.db_name = os.path.basename(wsm_msg_payloads_folder)

            self.wsm_msg_payloads_to_disk = wsm_msg_payloads_to_disk
            self.wsm_msg_payloads_use_mongodb = wsm_msg_payloads_use_mongodb
            self.use_wsm_transaction_time = use_wsm_transaction_time
            self.cdb_db = cdb_db
            self.domain_sub_list = domain_sub_list

    #    @cherrypy.tools.accept(media='text/plain')
    #     def GET(self):
    #         return cherrypy.session['mystring']


        def log_event(self, event_text):

            if self.use_wsm_transaction_time:
                index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"
            else:
                index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"

            splunk_event = index_time + " " + event_text
            self.print_xml_single_instance_mode(self.device_name, splunk_event)
            logging.debug("******** WS_M Logging event:" + str(splunk_event))

        def print_xml_single_instance_mode(self, host, event):
            print "<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)

        exposed = True

        #@cherrypy.tools.accept(media='text/plain')
        def POST(self):

            resp = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">
    <env:Body>
        <status>received push</status>
    </env:Body>
</env:Envelope>
"""

            try:
                push_req = cherrypy.request.body.read()


                logging.debug(str(cherrypy.request.headers))
                logging.debug("******** Recevied psush request:" + push_req)

                doc = lxml.etree.fromstring(push_req)

                nss = {"wsman": "http://schemas.xmlsoap.org/ws/2005/02/management", "trans": "http://www.datapower.com/schemas/transactions", "dpg": "http://datapower-modular-input.jjjw420.github.com"}

                msg_id = ""
                domain_nl = doc.xpath("//dpg:Domain", namespaces=nss)
                if domain_nl is not None:
                    if len(domain_nl) > 0:
                        domain = domain_nl[0].text

                #print lxml.etree.tostring(doc, pretty_print=True)
                domain = ""
                domain_nl = doc.xpath("//dpg:Domain", namespaces=nss)
                if domain_nl is not None:
                    if len(domain_nl) > 0:
                        domain = domain_nl[0].text

                sub = ""
                sub_nl = doc.xpath("//dpg:Subscription", namespaces=nss)
                if sub_nl is not None:
                    if len(sub_nl) > 0:
                        sub = sub_nl[0].text


                logging.debug("******** Received message for Domain: %s and subscription: %s" % (domain, sub))

                if sub not in self.domain_sub_list:
                    logging.error("******** Will NOT log Received message for Domain %s and subscription %s as subscription not in sub_list(%s)." % (domain, sub, str(self.domain_sub_list)))
                    return resp
                else:
                    logging.debug("******** Will log Received message for Domain %s and subscription %s as subscription is in sub_list(%s)." % (domain, sub, str(self.domain_sub_list)))

                nl = doc.xpath("//trans:transaction[@tid]", namespaces=nss)
                if nl is not None:
                    for n in nl:

                        start_time_n = n.find("trans:start-time", namespaces=nss)
                        transaction_id_n = n.find("trans:transaction-id", namespaces=nss)
                        tid = ""

                        db_obj = {"device": self.device_name, "domain": domain}
                        if transaction_id_n is not None:
                            db_obj["transaction_id"] = transaction_id_n.text
                            tid = transaction_id_n.text
                        if start_time_n is not None:
                            start_time_utc = start_time_n.attrib["utc"]
                            db_obj["start_time_utc"] = start_time_utc

                        fs_req_msg = n.find("trans:request-message", namespaces=nss)
                        if fs_req_msg is not None:
                            if len(fs_req_msg) > 0:
                                if self.wsm_msg_payloads_to_disk > 0 or self.wsm_msg_payloads_use_mongodb > 0:
                                    try:

                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(fs_req_msg[0]),9))
                                        ins_id = uuid.uuid4()
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["request_message"] = msg_comp

                                            ins = self.cdb_db.insert(new_db_obj)
                                            ins_id = ins["_id"]

                                        else:
                                            msg_file = open("%s_%s_%s.dat" % (domain, tid, ins_id), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        fs_req_msg.remove(fs_req_msg[0])
                                        fs_req_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error("******** Exception occurred while inserting or writing FS Request message! Ex:" + str(ex))


                        fs_resp_msg = n.find("trans:response-message", namespaces=nss)
                        if fs_resp_msg is not None:
                            if len(fs_resp_msg) > 0:
                                if self.wsm_msg_payloads_to_disk > 0 or self.wsm_msg_payloads_use_mongodb > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(fs_resp_msg[0]),9))
                                        ins_id = uuid.uuid4()
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["response_message"] = msg_comp

                                            ins = self.cdb_db.insert(new_db_obj)
                                            ins_id = ins["_id"]
                                        else:
                                            msg_file = open("%s_%s_%s.dat" % (domain, tid, ins_id), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        fs_resp_msg.remove(fs_resp_msg[0])
                                        fs_resp_msg.text = ins_id


                                    except Exception, ex:
                                        logging.error( "******** Exception occurred while inserting or writing FS Response message:" + str(ex))


                        bs_req_msg = n.find("trans:backend-message/trans:request-message", namespaces=nss)
                        if bs_req_msg is not None:
                            if len(bs_req_msg) > 0:
                                if self.wsm_msg_payloads_to_disk > 0 or self.wsm_msg_payloads_use_mongodb > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(bs_req_msg[0]),9))
                                        ins_id = uuid.uuid4()
                                        if self.wsm_msg_payloads_use_mongodb > 0:

                                            new_db_obj = db_obj.copy()
                                            new_db_obj["backend-request-message"] = msg_comp

                                            ins = self.cdb_db.insert(new_db_obj)
                                            ins_id = ins["_id"]
                                        else:
                                            msg_file = open("%s_%s_%s.dat" % (domain, tid, ins_id), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        bs_req_msg.remove(bs_req_msg[0])
                                        bs_req_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error("******** Exception occurred while inserting or writing BS Request message" + str(ex))


                        bs_resp_msg = n.find("trans:backend-message/trans:response-message", namespaces=nss)
                        if bs_resp_msg is not None:
                            if len(bs_resp_msg) > 0:
                                if self.wsm_msg_payloads_to_disk > 0 or self.wsm_msg_payloads_use_mongodb > 0:
                                    try:
                                        msg_comp = base64.encodestring(zlib.compress(lxml.etree.tostring(bs_resp_msg[0]),9))
                                        ins_id = uuid.uuid4()
                                        if self.wsm_msg_payloads_use_mongodb > 0:
                                            new_db_obj = db_obj.copy()
                                            new_db_obj["backend-response-message"] = msg_comp

                                            ins = self.cdb_db.insert(new_db_obj)
                                            ins_id = ins["_id"]
                                        else:
                                            msg_file = open("%s.dat" % (ins_id), "wb")
                                            msg_file.write(msg_comp)
                                            msg_file.close()

                                        bs_resp_msg.remove(bs_resp_msg[0])
                                        bs_resp_msg.text = ins_id

                                    except Exception, ex:
                                        logging.error("******** Exception occurred while inserting or writing BS Response message" + str(ex))
                                        pass

                        #print lxml.etree.tostring(n, pretty_print=True)
#
#                         event_text = ""
#                         if self.wsm_msg_payloads_to_disk:
#                             event_text = 'msg_folder="%s" ' % self.db_name

                        for el in n:
                            ns_end = el.tag.find("}")
                            el_tag = el.tag
                            if ns_end > 0:
                                el_tag = el.tag[ns_end + 1:]

                            if el_tag == "backend-message":
                                el_tag = "be"

                            el_tag = el_tag.replace("-", "_")
                            if len(el) > 0:
                                for eel in el:
                                    eel_tag = eel.tag
                                    ns_end = eel.tag.find("}")
                                    if ns_end > 0:
                                        eel_tag = eel.tag[ns_end + 1:]

                                    eel_tag = eel_tag.replace("-", "_")
                                    if self.wsm_msg_payloads_to_disk > 0:
                                        if eel.text is None:
                                            event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag,  "")
                                        else:
                                            event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag, eel.text.replace("\n", ""))

                                        if len(eel.attrib) > 0:
                                            for el_a, el_a_v in eel.attrib.items():
                                                event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag + "_" + el_a, el_a_v.replace("\n", ""))
                                    else:

                                        if eel.text is None:
                                            event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag,  "")
                                        else:
                                            event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag, eel.text.replace("\n", ""))

                                        if len(eel.attrib) > 0:
                                            for el_a, el_a_v in eel.attrib.items():
                                                event_text = event_text + '%s="%s" ' % (el_tag + "_" + eel_tag + "_" + el_a, el_a_v.replace("\n", ""))

                            else:
                                if el.text is None:
                                    event_text = event_text + '%s="%s" ' % (el_tag,  "")
                                else:
                                    event_text = event_text +  '%s="%s" ' % (el_tag, el.text.replace("\n", ""))

                                if len(el.attrib) > 0:
                                    for el_a, el_a_v in el.attrib.items():
                                        event_text = event_text + '%s="%s" ' % (el_tag + "_" + el_a, el_a_v.replace("\n", ""))

                        self.log_event(event_text)

            except Exception, ex:
                logging.error("******** Exception occurred in WSM Push thread! Exception:" + str(ex))


                #new_db_obj["request-message"] =

            return resp

    def __init__(self, thread_id, thread_name, input_name, splunk_host, device_name,
                 device_host, soma_port, soma_user, soma_user_password, use_wsm, wsm_push_server_host, wsm_push_server_port,
                 use_wsm_transaction_time, wsm_push_max_elements,
                 wsm_msg_payloads_to_disk, wsm_msg_payloads_folder, wsm_msg_payloads_use_mongodb,
                 domain_list, **kw):
        threading.Thread.__init__(self)

        logging.debug("******** Started WS-M Push server Thread %s for input %s." % (thread_id, input_name))

        self.setName(thread_id)
        self.thread_id = thread_id
        self.thread_name = thread_name
        self.input_name = input_name
        self.splunk_host = splunk_host
        self.device_name = device_name
        self.device_host = device_host
        self.soma_port = soma_port
        self.soma_user = soma_user
        self.soma_user_password = soma_user_password
        self.use_wsm = use_wsm
        self.wsm_push_server_host = wsm_push_server_host
        self.wsm_push_server_port = wsm_push_server_port
        self.wsm_msg_payloads_to_disk = wsm_msg_payloads_to_disk
        self.wsm_msg_payloads_folder = wsm_msg_payloads_folder
        self.wsm_msg_payloads_use_mongodb = wsm_msg_payloads_use_mongodb
        #self.wsm_push_server_thread_per_domain = wsm_push_server_thread_per_domain
        self.use_wsm_transaction_time = use_wsm_transaction_time
        self.wsm_push_max_elements = wsm_push_max_elements
        self.domain_list = domain_list
        self.kw = kw

        self.soma_url = "https://{device_host}:{soma_port}/service/mgmt/3.0".format(device_host=device_host, soma_port=soma_port)
        self.domain_sub_dict = {}
        self.domain_sub_list = []
        self.session = requests.Session()
        self.session.auth = (self.soma_user, self.soma_user_password)
        self.session.verify = False

        self.cherry_py_conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')],
            }
        }

        cherrypy.config.update({'server.socket_host': '0.0.0.0',
                                'server.socket_port': self.wsm_push_server_port})

        self.current_date =  datetime.datetime.now().strftime("%Y%m%d")
        self.current_cdb_folder = os.path.join(wsm_msg_payloads_folder, self.current_date)

        if self.wsm_msg_payloads_use_mongodb:
#             self.cdb_db = ThreadSafeDatabase(self.current_cdb_folder)
#
#             if self.cdb_db.exists(self.current_cdb_folder):
#                 self.cdb_db.open(self.current_cdb_folder)
#             else:
#                 self.cdb_db.create()
            pass



    wsm_push_subscription_req = """<env:Envelope xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:dpg="http://datapower-modular-input.jjjw420.github.com">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/domain)</wsa:To>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Subscribe</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">51200</wsman:MaxEnvelopeSize>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsman:SelectorSet Name="dp-domain">
         <wsman:Selector Name="domain">{domain}</wsman:Selector>
      </wsman:SelectorSet>
   </env:Header>
   <env:Body>
      <wse:Subscribe>
         <wse:Delivery Mode="http://schemas.xmlsoap.org/ws/2005/02/management/Events">
            <wse:NotifyTo>
               <wsa:Address>{wsm_push_address}</wsa:Address>
                  <wsa:ReferenceProperties>
                     <dpg:Domain>{domain}</dpg:Domain>
                     <dpg:Subscription>{msg_id}</dpg:Subscription>
                </wsa:ReferenceProperties>
            </wse:NotifyTo>
            <wsman:MaxElements>{wsm_max_elements}</wsman:MaxElements>
            <wsman:MaxTime>{push_server_timeout}</wsman:MaxTime>
         </wse:Delivery>
         <wse:Expires>{expires}</wse:Expires>
      </wse:Subscribe>
   </env:Body>
</env:Envelope>
"""


    def subscribe_push(self, domain, expires="PT15M", wsm_max_elements=100, push_server_timeout=60, wsm_push_server_host=None, wsm_push_server_port=14014):
        """

        """

        if wsm_push_server_host is None:
            logging.error("******** Push server host is none.")
            return False

        msg_id = uuid.uuid4()
        wsm_push_address = "http://{wsm_push_server_host}:{wsm_push_server_port}/".format(wsm_push_server_host=wsm_push_server_host, wsm_push_server_port=wsm_push_server_port)
        soma_wsm_push_subscription_req  = self.wsm_push_subscription_req.format(domain=domain, expires=expires, msg_id=str(msg_id), push_server_timeout=push_server_timeout, wsm_push_address=wsm_push_address,wsm_max_elements=wsm_max_elements)

        try:
            r = self.session.post(self.soma_url, data=soma_wsm_push_subscription_req)

            if r.status_code != 200:
                logging.error("******** Error while doing push subscription.  Status_Code: %s" % str(r.status_code))
            else:
                doc = lxml.etree.fromstring(r.content)

                nss = {"wsen": "http://schemas.xmlsoap.org/ws/2004/09/enumeration"}

                nl = doc.xpath("//wsen:EnumerationContext", namespaces=nss)
                if len(nl) > 0:
                    enumeration_context = nl[0].text
                    self.domain_sub_dict[domain] = enumeration_context
                    self.domain_sub_list.append(str(msg_id))
                    logging.debug("******** Push subscribe OK.  Sub: %s" % (enumeration_context))
                    return True
                else:
                    logging.error("******** Error while doing push subscription.  No EnumerationContext?? Response: %s" % str(r.content))

        except Exception, ex:
            logging.error("******** Exception while doing push subscription.  Exception: %s" % str(ex))

        return False

    wsm_renew_push_subscription_req = """<env:Envelope xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:env="http://www.w3.org/2003/05/soap-envelope">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>{enumeration_context}</wse:Identifier>
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Renew</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">51200</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wse:Renew>
         <wsen:Expires>{expires}</wsen:Expires>
      </wse:Renew>
   </env:Body>
</env:Envelope>
"""

    def renew_push_subscription(self, domain, enumeration_context, expires="PT15M"):
        """

        """

        soma_wsm_renew_subscription_req  = self.wsm_renew_push_subscription.format(domain=domain, expires=expires, msg_id=uuid.uuid4(), enumeration_context=enumeration_context)

        try:
            r = self.session.post(self.soma_url, data=soma_wsm_renew_subscription_req)

            if r.status_code != 200:
                logging.error("******** Error while renewing push subscription.  Status_Code: %s" % str(r.status_code))
            else:
                doc = lxml.etree.fromstring(r.content)

                nss = {"wsen": "http://schemas.xmlsoap.org/ws/2004/09/enumeration"}

                nl = doc.xpath("//RenewResponse", namespaces=nss)
                if len(nl) > 0:
                    logging.debug("******** Renew of %s OK." % str(enumeration_context))
                    return True
                else:
                    logging.error("******** Error while doing pull subscription.  No EnumerationContext?? Response: %s" % str(r.content))

        except Exception, ex:
            logging.error("******** Exception while doing pull subscription.  Exception: %s" % str(ex))

        return False

    wsm_push_unsubscribe_req = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>{enumeration_context}</wse:Identifier>
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Unsubscribe</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">51200</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wse:Unsubscribe>
         <wsen:EnumerationContext>{enumeration_context}</wsen:EnumerationContext>
      </wse:Unsubscribe>
   </env:Body>
</env:Envelope>
"""

    def unsubscribe_push_subscription(self, domain, enumeration_context):
        """

        """

        try:
            soma_wsm_unsub_req  = self.wsm_push_unsubscribe_req.format(domain=domain, msg_id=uuid.uuid4(), enumeration_context=enumeration_context)
            r = self.session.post(self.soma_url, data=soma_wsm_unsub_req)

            if r.status_code != 200:
                logging.error("******** Error while un-subscribing push subscription.  Status_Code: %s" % str(r.status_code))
            else:
                logging.debug("******** Unsubscribed for domain: %s " % (domain))
                return True
        except Exception, ex:
            logging.error("******** Exception while doing pull subscription.  Exception: %s" % str(ex))

        return False


    def log_event(self, event_text):

        if self.use_wsm_transaction_time:
            index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"
        else:
            index_time = "[" + datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + " " + time.strftime("%z") + "]"

        splunk_event = index_time + " " + event_text
        self.print_xml_single_instance_mode(self.device_name, splunk_event)

    def print_xml_single_instance_mode(self, host, event):
        print "<stream><event><data>%s</data><host>%s</host></event></stream>" % (cgi.escape(event), host)

#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_value, traceback):
#         logging.debug("Exit called..")
#         cherrypy.engine.exit()
#         for domain in self.domain_list:
#             enumeration_context = ""
#             if self.domain_sub_dict.has_key(domain):
#                 enumeration_context = self.domain_sub_dict[domain]
#                 logging.debug("in Exit.  Unsubscribing..")
#                 self.unsubscribe_push_subscription(domain, self.enumeration_context)

    def __del__(self, exc_type, exc_value, traceback):
        logging.debug("******** delete called..")
        cherrypy.engine.exit()
        for domain in self.domain_list:
            enumeration_context = ""
            if self.domain_sub_dict.has_key(domain):
                enumeration_context = self.domain_sub_dict[domain]
                logging.debug("******** in dellete.  Unsubscribing..")
                self.unsubscribe_push_subscription(domain, self.enumeration_context)


    def run(self):

        logging.debug("******** WSM in run()")

        for domain in self.domain_list:
            self.subscribe_push(domain, wsm_max_elements=self.wsm_push_max_elements, wsm_push_server_host=self.wsm_push_server_host, wsm_push_server_port=self.wsm_push_server_port)
        sub_time = time.time()

        logging.debug("HERE:" + str(cherrypy.engine.state))

        try:
            cherrypy.engine.exit()
        except:
            pass

        #cherrypy.quickstart(self.WSMPushRestService(self.device_name, self.domain_sub_list, self.use_wsm_transaction_time, self.wsm_msg_payloads_to_disk, self.current_cdb_folder, self.wsm_msg_payloads_use_mongodb, self.cdb_db), '/', self.cherry_py_conf)
        cherrypy.tree.mount(self.WSMPushRestService(self.device_name, self.domain_sub_list, self.use_wsm_transaction_time, self.wsm_msg_payloads_to_disk, self.current_cdb_folder, self.wsm_msg_payloads_use_mongodb, self.cdb_db), '/', self.cherry_py_conf)
        cherrypy.engine.signal_handler.subscribe()
        cherrypy.engine.start()

        logging.debug("******** WSM in run() - started server.")
        while True:
            try:
                logging.debug("******** WSM in run() - while true loop.")
                file_pid = str(open("/tmp/%s_wsm_%s_current.pid" % (self.input_name.replace("://", "-"), str(self.thread_name)), "r").read())
                logging.debug("******** WSM this pid:" + str(self.thread_id) + " File pid:" + str(file_pid))
                if self.thread_id != file_pid.strip():
                    logging.debug("******* WSM Stopping... this pid:" + str(self.getName()) + " File pid:" + str(file_pid))
                    done = True
                    cherrypy.engine.exit()

                    for domain in self.domain_list:
                        enumeration_context = ""
                        if self.domain_sub_dict.has_key(domain):
                            enumeration_context = self.domain_sub_dict[domain]
                            self.unsubscribe_push_subscription(domain, enumeration_context)

                    return
                else:
                    logging.debug("********% WS-M Not stopping...")
                    pass

                if (time.time() - sub_time) > 480:
                    logging.debug("******** Over 480 seconds.  Renewing.")
                    for domain in self.domain_list:
                        enumeration_context = ""
                        if self.domain_sub_dict.has_key(domain):
                            enumeration_context = self.domain_sub_dict[domain]
                        if enumeration_context == "":
                            logging.error("******** NO Domain subscription found to renew? Domain:" + domain)
                        else:
                            if not self.renew_push_subscription(domain, enumeration_context):
                                logging.error("******** Renew of subscription for domain %s failed." % (domain))
                            else:
                                logging.debug("******** Renew of subscription for domain %s OK." % (domain))
                                sub_time = time.time()

                if self.current_date !=  datetime.datetime.now().strftime("%Y%m%d"):
                    logging.debug("******** WSM in run() - Date changed. Starting new thread and db.")
                    self.current_date =  datetime.datetime.now().strftime("%Y%m%d")
                    cherrypy.engine.exit()

                    if self.wsm_msg_payloads_use_mongodb:
                        logging.debug("******** WSM in run() - Date changed. Closing db")
#                         self.cdb_db.close()
#                         self.current_cdb_folder = os.path.join(self.wsm_msg_payloads_folder, self.current_date)
#                         self.cdb_db = ThreadSafeDatabase(self.current_cdb_folder)
#
#                         logging.debug("******** WSM in run() - Date changed. creating or opening db")
#                         if self.cdb_db.exists(self.current_cdb_folder):
#                             self.cdb_db.open(self.current_cdb_folder)
#                         else:
#                             self.cdb_db.create()

                        logging.debug("******** WSM in run() - Date changed. DB changed OK.")

                        #cherrypy.quickstart(self.WSMPushRestService(self.device_name, self.domain_sub_list, self.use_wsm_transaction_time,  self.wsm_msg_payloads_to_disk, self.current_cdb_folder, self.wsm_msg_payloads_use_mongodb, self.cdb_db), '/', self.cherry_py_conf)
                        cherrypy.tree.mount(self.WSMPushRestService(self.device_name, self.domain_sub_list, self.use_wsm_transaction_time, self.wsm_msg_payloads_to_disk, self.current_cdb_folder, self.wsm_msg_payloads_use_mongodb, self.cdb_db), '/', self.cherry_py_conf)
                        cherrypy.engine.signal_handler.subscribe()
                        cherrypy.engine.start()


            except Exception, ex:
                logging.error("******** Exception occurred in WS-M Push thread.  Stopping. Exception:" + str(ex))
                done = True
                self.exit()

            time.sleep(60)

# prints validation error data to be consumed by Splunk
def print_validation_error(s):
    print "<error><message>%s</message></error>" % xml.sax.saxutils.escape(s)

def usage():
    print "usage: %s [--scheme|--validate-arguments]"
    logging.error("Incorrect Program Usage")
    sys.exit(2)

def do_scheme():
    logging.debug("MQINPUT: DO scheme..")
    print SCHEME

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_input_config():
    config = {}

    try:
        # read everything from stdin
        config_str = sys.stdin.read()

        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            logging.debug("XML: found configuration")
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    logging.debug("XML: found stanza " + stanza_name)
                    config["name"] = stanza_name

                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        logging.debug("XML: found param '%s'" % param_name)
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            logging.debug("XML: '%s' -> '%s'" % (param_name, data))

        checkpnt_node = root.getElementsByTagName("checkpoint_dir")[0]
        if checkpnt_node and checkpnt_node.firstChild and \
           checkpnt_node.firstChild.nodeType == checkpnt_node.firstChild.TEXT_NODE:
            config["checkpoint_dir"] = checkpnt_node.firstChild.data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."


    except: # catch *all* exceptions
        e = sys.exc_info()[1]
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_validation_config():
    val_data = {}

    # read everything from stdin
    val_str = sys.stdin.read()

    # parse the validation XML
    doc = xml.dom.minidom.parseString(val_str)
    root = doc.documentElement

    logging.debug("XML: found items")
    item_node = root.getElementsByTagName("item")[0]
    if item_node:
        logging.debug("XML: found item")

        name = item_node.getAttribute("name")
        val_data["stanza"] = name

        params_node = item_node.getElementsByTagName("param")
        for param in params_node:
            name = param.getAttribute("name")
            logging.debug("Found param %s" % name)
            if name and param.firstChild and \
               param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                val_data[name] = param.firstChild.data

    return val_data

if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":
            do_scheme()
        elif sys.argv[1] == "--validate-arguments":
            do_validate()
        else:
            usage()
    else:
        do_run()

    sys.exit(0)
