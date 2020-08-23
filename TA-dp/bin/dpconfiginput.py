'''
IBM Websphere Datapower Modular Input for Splunk
Hannes Wagener - 2016

DISCLAIMER
You are free to use this code in any way you like, subject to the
Python & IBM disclaimers & copyrights. I make no representations
about the suitability of this software for any purpose. It is
provided "AS-IS" without warranty of any kind, either express or
implied.

'''
from __future__ import print_function
 
import sys
import argparse
import datetime
import json
import logging
import requests
import splunklib.client 
import splunklib.results
import splunklib.modularinput
import time

# Initialize the root logger with a StreamHandler and a format message:
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class DPConfigInput(splunklib.modularinput.Script):
    
    def get_scheme(self):
        # Returns scheme.
        scheme = splunklib.modularinput.Scheme("IBM Websphere Datapower Configuration")
        scheme.description = "IBM Websphere Datapower Configuration Input for Splunk."
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

        clear_index_argument = splunklib.modularinput.Argument("clear_index")
        clear_index_argument.data_type = splunklib.modularinput.Argument.data_type_number
        clear_index_argument.title = "Clear index"
        clear_index_argument.description = "Clear the index on every execution."
        clear_index_argument.required_on_create = True
        clear_index_argument.required_on_edit = False
        scheme.add_argument(clear_index_argument)
        


        # interval_argument = splunklib.modularinput.Argument("interval")
        # interval_argument.data_type = splunklib.modularinput.Argument.data_type_string
        # interval_argument.title = "Interval"
        # interval_argument.description = "How often to run the MQ input script. Interval or cron expression."
        # interval_argument.required_on_create = False
        # interval_argument.required_on_edit = False
        # scheme.add_argument(interval_argument)

        return scheme

    def validate_input(self, validation_definition):
        # Validates input.
        rest_port = int(validation_definition.parameters["rest_port"])
        
        if rest_port <= 0 or rest_port > 65535:
            raise ValueError("REST port must be set to a valid port number between 0 and 65535. Port number:%d." % rest_port)
    
    def get_dp_config_types(self, rest_session, device_host, rest_port):
        
        logging.debug("in get_dp_config_types...")
        get_config_types_uri = "/mgmt/config/"
        get_config_types_url = self.rest_url.format(device_host=device_host, rest_port=rest_port, rest_uri=get_config_types_uri)
        logging.debug("get_config_types_url: " + get_config_types_url)
        r = rest_session.get(get_config_types_url)
        if r.status_code != 200:
            logging.error("Get config types failed. Status code:%i Response: %s." % (r.status_code, r.content))
            return None
        logging.debug("after fetch  config types")

        config_types = json.loads(r.content)
        logging.debug("after json loads config_types")
        return config_types

    def get_dp_domains(self, rest_session, device_host, rest_port):

        logging.debug("in get_dp_domains...")
        get_domains_uri = "/mgmt/status/default/DomainStatus"
        domain_status_url = self.rest_url.format(device_host=device_host, rest_port=rest_port, rest_uri=get_domains_uri)
        logging.debug(domain_status_url)
        r = rest_session.get(domain_status_url)
        if r.status_code != 200:
            logging.error("Get domain status failed. Status code:%i Response: %s." % (r.status_code, r.content))
            return None
        domain_list = []

        logging.debug("content: <" + r.content.decode("utf-8") + ">")
        
        domain_status_resp = json.loads(r.content)
        logging.debug("after json:" + str(domain_status_resp))
        if "DomainStatus" in domain_status_resp:

            if isinstance(domain_status_resp["DomainStatus"], list):
                for domain_status in domain_status_resp["DomainStatus"]:
                    if "Domain" in domain_status:
                        domain_list.append(domain_status["Domain"])
            elif isinstance(domain_status_resp["DomainStatus"], dict):
                domain_status = domain_status_resp["DomainStatus"]
                if "Domain" in domain_status:
                    domain_list.append(domain_status["Domain"])

            return domain_list    
        else:
            logging.error("No DomainStatus element. Status code:%i Response: %s." % (r.status_code, r.content))
            return None

    def get_dp_config_type(self, rest_session, device_host, rest_port, rest_uri):

        logging.debug("in get_dp_config_type.") 
        logging.debug("device_host:" + device_host) 
        logging.debug("rest_port:" + str(rest_port)) 
        logging.debug("rest_uri:" + str(rest_uri)) 
        get_config_type_url = self.rest_url.format(device_host=device_host, rest_port=rest_port, rest_uri=rest_uri)
        logging.debug("get_config_type_url:" + get_config_type_url)

        r = rest_session.get(get_config_type_url)
        if r.status_code != 200:
            logging.error("Get config type failed. Uri: %s Status code:%i Response: %s." % (rest_uri, r.status_code, r.content))
            return None
        logging.debug("Status code:" + str(r.status_code))
        config_type = json.loads(r.content)

        return config_type

    def get_dp_configs(self, input_name, device_name, device_host, rest_port, rest_user, rest_user_password, interval, index, clear_index, ew):
        logging.info("Creating REST session to device %s (%s:%s)." % (device_name, device_host, rest_port))
   
        self.rest_url = "https://{device_host}:{rest_port}{rest_uri}"
        rest_session = requests.Session()
        rest_session.auth = (rest_user, rest_user_password)
        rest_session.verify = False

        rest_session.headers = {"Content-Type": "application/json", "Accept": "application/json"}

        domain_list = self.get_dp_domains(rest_session, device_host, rest_port)
        config_types = self.get_dp_config_types(rest_session, device_host, rest_port)
        default_domain_only_types = ["AuditLog","CertMonitor","CRLFetch","DNSNameService","Domain",
                                    "ErrorReportSettings","EthernetInterface","HostAlias","ILMTAgent","InteropService","Language",
                                    "LinkAggregation","Luna","MgmtInterface","NetworkSettings","NFSClientSettings","NTPService",
                                    "ODR","ODRConnectorGroup","QuotaEnforcementServer","RADIUSSettings","RaidVolume","RBMSettings",
                                    "RestMgmtInterface","SecureBackupMode","SNMPSettings","SQLRuntimeSettings","SSHService",
                                    "StandaloneStandbyControl","StandaloneStandbyControlInterface","SystemSettings","TelnetService",
                                    "Throttler","TimeSettings","User","UserGroup","VLANInterface","WebGUI","xmltrace","ZHybridTargetControlService"]
             
        if clear_index:
            logging.debug("get_dp_configs clear_index true")
            idx = self.service.indexes[index]
            idx.clean()
            time.sleep(20)
        else:
            logging.debug("get_dp_configs clear_index false")

        for domain in domain_list:
            # for each domain fetch each  type of config
            logging.debug("Domain start:" + domain)

            if "_links" in config_types:
                logging.debug("_links in config_types.  config type: " + str(config_types))    
                for c_type, c_uri in config_types["_links"].items():
                    logging.debug("Domain: " + domain + " _links items:" + str(config_types["_links"].items()))
                    logging.debug("domain: " + domain + " ctype: " + str(c_type) + " c_uri: " + str(c_uri))
                    if c_type == "self":
                        continue

                    if domain != "default":
                        if c_type in default_domain_only_types:
                            continue

                    logging.debug("before get_dp_config_type()")
                    rest_uri = c_uri["href"]
                    rest_uri = rest_uri.format(domain=domain)
                    logging.debug("after rest_uri format. rest_uri:" + rest_uri)
                    

                    config_type = self.get_dp_config_type(rest_session, device_host, rest_port, rest_uri)
                    if config_type is None:
                        logging.error("config_type is None! An exception occurred.")
                        logging.error("Failed on rest_uri:" + rest_uri)
                        continue
                    
                    if c_type in config_type:
                        logging.debug(str(type(config_type[c_type])))
                        if not isinstance(config_type[c_type], dict):
                            logging.debug("is list??")
                            logging.debug(str(config_type[c_type]))
                            for c_type_config in config_type[c_type]:
                                logging.debug("in ctype - list")
                                new_obj = {}
                                new_obj["device"] = device_name
                                new_obj["domain"] = domain
                                new_obj["type"] = c_type
                                if "name" in c_type_config:
                                    name = c_type_config["name"]
                                    new_obj["name"] = name

                                if "_links" in c_type_config:
                                    del(c_type_config["_links"])
                                    
                                new_obj[c_type] = c_type_config
                                logging.debug("list config_type: " + str(config_type))
                                logging.debug("list c_type: " + str(c_type))
                                logging.debug("list config_type[c_type]:" + str(config_type[c_type]))

                                new_obj_str = json.dumps(new_obj)
                                logging.debug("event text:" + new_obj_str)
                                event = splunklib.modularinput.Event()
                                event.stanza = input_name
                                event.data = new_obj_str

                                ew.write_event(event)
                        else:
                            logging.debug("in ctype - not list")
                            new_obj = {}
                            new_obj["device"] = device_name
                            new_obj["domain"] = domain
                            new_obj["type"] = c_type
                            if "name" in config_type[c_type]:
                                name = config_type[c_type]["name"]
                                new_obj["name"] = name
                            logging.debug("cinfig_type: " + str(config_type))
                            logging.debug("c_type: " + str(c_type))
                            logging.debug("config_type[c_type]:" + str(config_type[c_type]))

                            if "_links" in config_type[c_type]:
                                del(config_type[c_type]["_links"])

                            new_obj[c_type] = config_type[c_type]           

                            new_obj_str = json.dumps(new_obj)
                            logging.debug("event text:" + new_obj_str)
                            event = splunklib.modularinput.Event()
                            event.stanza = input_name
                            event.data = new_obj_str

                            ew.write_event(event)
                    else:
                        logging.debug("No config. %s" % str(c_type))        
            else:
                logging.error("No _links element in config_types. ")
            logging.debug("Domain end:" + domain)

    def stream_events(self, inputs, ew):
        # Splunk Enterprise calls the modular input, 
        # streams XML describing the inputs to stdin,
        # and waits for XML on stdout describing events.
        logging.debug(str(inputs))
        logging.debug(str(inputs.inputs ))
        for input_name, input_item in inputs.inputs.items():
            device_name = input_item["device_name"]
            device_host = input_item["device_host"]

            rest_port = int(input_item["rest_port"])
            rest_user = input_item["rest_user"]
            rest_user_password = input_item["rest_user_password"]
            interval = input_item["interval"]
            index = input_item["index"]
            clear_index = int(input_item["clear_index"])
            logging.debug("clear_index:" + str(clear_index))
            if clear_index is not None:
                
                if clear_index == 1:
                    clear_index = True
                else:
                    clear_index = False
            else:
                clear_index = False

            logging.debug(str(input_item))
            interval = "0"
            self.get_dp_configs(input_name, device_name, device_host, rest_port, rest_user, rest_user_password, interval, index, clear_index, ew)

if __name__ == "__main__":
    sys.exit(DPConfigInput().run(sys.argv))
 