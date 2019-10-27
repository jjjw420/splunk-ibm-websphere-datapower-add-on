#!/opt/splunk/bin/python
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
import splunk.Intersplunk
import splunklib.client 
import splunklib.results
import sys
from collections import OrderedDict

index_name="esb_dp_config"             

"""

"""
(isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)


if isgetinfo:
    splunk.Intersplunk.outputInfo(True, False, False, False, None, False)

# valid_parms = ["text", "element_value", "element_type", "object_type", "domain", "device", "follow_dependencies", "output_dependency_tree", "only_show_top_levels"]
# if len(sys.argv) > len(valid_parms):
#     splunk.Intersplunk.parseError("Too many arguments provided.")

# i = 1
# parm_dict = {}
# while i < len(sys.argv):
#     arg = sys.argv[i]
#     if arg.count("=") == 1:
#         (parm, value) = arg.split("=")
#         if parm not in valid_parms:
#             splunk.Intersplunk.parseError("Invalid argument. Valid options are text=<text>, element_value=<value>, element_type=<element_type>, object_type=<object_type>, domain, device, follow_dependencies, output_dependency_tree.")

#         # if parm == "bloblimit" or parm == "extractbloblimit":
#         #     try:
#         #         int(value.strip())
#         #     except:
#         #         splunk.Intersplunk.parseError("Invalid argument vale for bloblimit or extractbloblimit.  Must be an integer value.")

#         if parm == "follow_dependencies" or parm == "output_dependency_tree" or parm == "only_show_top_levels":
#             if value.strip().lower() != "true" and value.strip().lower() != "false":
#                 splunk.Intersplunk.parseError("Invalid argument value for follow_dependencies, only_show_top_levels or output_dependency_tree.  Must be either true or false.")

#         parm_dict[parm] = value

#     else:
#         if arg.count("=") > 1 or arg.count("=") <= 0:
#             splunk.Intersplunk.parseError("Invalid argument. Valid options are text=<text>, element_value=<value>, element_type=<element_type>, object_type=<object_type>, domain, device, follow_dependencies, output_dependency_tree.")

#     i = i + 1    

messages = {}
settings = {}
results = splunk.Intersplunk.readResults(settings=settings, has_header=True)

s_token = settings['sessionKey']

i = 0
new_results = []

tops = []
up_saved_resps = {}
down_saved_resps = {}

service_name_dict = {}
try:

    # service = splunklib.client.connect(
    #     host=HOST,
    #     port=PORT,
    #     username=USERNAME,
    #     password=PASSWORD)

    service = splunklib.client.connect(token=s_token)
    object_name = None
    device = None
    domain = None

    for res in results:
        sys.stderr.write("got result!")
        if res.has_key("device"):
            device = res["device"]
        
        if res.has_key("domain"):
            domain = res["domain"]

        if res.has_key("object_name"):
            object_name = res["object_name"]
        else:
            if res.has_key("Name"):
                object_name = res["Name"]
            else:
                if res.has_key("name"):
                    object_name = res["name"]
        
        service_name = ""
        service_type = ""
        if service_name_dict.has_key((device,domain,object_name)):

            (service_type, service_name) = service_name_dict[(device,domain,object_name)]
        else:
            query = """search earliest=-30d index=esb_dp_config %s device=%s sourcetype=_json domain=%s (type=MultiProtocolGateway OR type=WSGateway OR type=XMLFirewallService OR type=WebAppFW OR type=WSEndpointRewritePolicy)
|spath | eval type=if(type="WSEndpointRewritePolicy", "WSGateway", type)
""" % (object_name, device, domain)
            kwargs_oneshot = { "count": 0 }
            config_search_response = service.jobs.oneshot(query, **kwargs_oneshot)
            config_resps = splunklib.results.ResultsReader(config_search_response)

            
            if config_resps is not None:
                for config_resp in config_resps:
                    if config_resp.has_key("name"):
                        res["configrespsname"] =  "yes" 
                        #service_name = service_name + " " + config_resp["name"]
                        service_name = str(config_resp["name"])
                    if config_resp.has_key("type"):
                        if type(config_resp["type"]) == type([]):
                            service_type = str(config_resp["type"][0])
                        else:
                            service_type = str(config_resp["type"])
            sys.stderr.write("type: " + str(service_type))
            sys.stderr.write("name: " + str(service_name))
            service_name = service_name.strip()
            service_type = service_type.strip()
            service_name_dict[(device,domain,object_name)] = (service_type, service_name)
     
        res["service_name"] = service_name
        res["service_type"] = service_type

except Exception, ex:
    sys.stderr.write("Exception occurred. Exception:{}".format(str(ex)))
    splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))

splunk.Intersplunk.outputResults(results, messages=messages)


