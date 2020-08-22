#!/opt/splunk/bin/python
'''
IBM Websphere Datapower Modular Input for Splunk
IBm Datapower Configuration search and display command.
Can follow IBM Datapower object dependencies and print the IBM Datapower object hiearchy.
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
import json
from collections import OrderedDict
import logging

import splunk.Intersplunk
import splunklib.client 
import splunklib.results

logger = logging.getLogger("dp_config_search")
logger.setLevel(logging.DEBUG)

DEFAULT_INDEX = "main"             
#TODO: cater for reading the index from the events or parms
index_name = DEFAULT_INDEX

"""
Options:

1.) With events:

follow_dependencies=true/false - find top level documents and recurse down.
only_show_top_levels=true/false - only print top level documents found
output_dependency_tree=true/false - output new events that can be used for drawing force-directed diagram


2.) Without events:

search_text - Any arb text. eg 256, XML*
search_element_value - search "value" field(including children. eg. , "elements{}.type"). 
search_element_type - search "type" field(including children. eg. , "elements{}.type") eg. CacheSize, Action
search_object_type - search "type" field(excluding children). eg. WSGateway, HTTPSourceProtocolHandler, CryptoKey
search_domain - only include domains listed
search_device - only include devices listed


"""
(isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)


if isgetinfo:
    splunk.Intersplunk.outputInfo(False, False, False, False, None, False)

valid_parms = ["text", "element_value", "element_type", "object_type", "domain", "device", "follow_dependencies", "output_dependency_tree", "only_show_top_levels"]
if len(sys.argv) > len(valid_parms):
    splunk.Intersplunk.parseError("Too many arguments provided.")

i = 1
parm_dict = {}
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg.count("=") == 1:
        (parm, value) = arg.split("=")
        if parm not in valid_parms:
            splunk.Intersplunk.parseError("Invalid argument. Valid options are text=<text>, element_value=<value>, element_type=<element_type>, object_type=<object_type>, domain, device, follow_dependencies, output_dependency_tree.")

        # if parm == "bloblimit" or parm == "extractbloblimit":
        #     try:
        #         int(value.strip())
        #     except:
        #         splunk.Intersplunk.parseError("Invalid argument vale for bloblimit or extractbloblimit.  Must be an integer value.")

        if parm == "follow_dependencies" or parm == "output_dependency_tree" or parm == "only_show_top_levels":
            if value.strip().lower() != "true" and value.strip().lower() != "false":
                splunk.Intersplunk.parseError("Invalid argument value for follow_dependencies, only_show_top_levels or output_dependency_tree.  Must be either true or false.")

        parm_dict[parm] = value

    else:
        if arg.count("=") > 1 or arg.count("=") <= 0:
            splunk.Intersplunk.parseError("Invalid argument. Valid options are text=<text>, element_value=<value>, element_type=<element_type>, object_type=<object_type>, domain, device, follow_dependencies, output_dependency_tree.")

    i = i + 1    

messages = {}
settings = {}
results = splunk.Intersplunk.readResults(settings=settings, has_header=True)

s_token = settings['sessionKey']

i = 0
new_results = []

tops = []
up_saved_resps = {}
down_saved_resps = {}
obj_domain = None
obj_device = None

def recurse_down(in_obj, obj_name=None, obj_type=None):
    global obj_domain
    global obj_device
    global down_saved_resps
    sys.stderr.write("\nIN recurse_down&&&!!\n obj_device: %s obj_domain: %s obj_name: %s obj_type: %s" % (obj_device, obj_domain, obj_name, obj_type))
    #obj_name = None
    #obj_type = None
    if "domain" in in_obj:
        obj_domain = in_obj["domain"]
    if "device" in in_obj:
        obj_device = in_obj["device"]
    if "name" in in_obj:
        obj_name = in_obj["name"]
    if "type" in in_obj:
        obj_type = in_obj["type"]        

    sys.stderr.write("\nobj: " + str(in_obj) )
    sys.stderr.write("\nIN recurse_down After init !!\n obj_device: %s obj_domain: %s obj_name: %s obj_type: %s" % (obj_device, obj_domain, obj_name, obj_type))
    for (k, v) in in_obj.items():
        if k in ["domain", "name", "type", "device"]:
            continue
        
        if isinstance(v, dict):
            recurse_down(v, obj_name, obj_type)

        if isinstance(v, list):
            for v_i in v:
                if isinstance(v_i, dict):
                    recurse_down(v_i,  obj_name, obj_type)
                if isinstance(v_i, list):
                    for v_ii in v_i:
                        recurse_down(v_ii, obj_name, obj_type)

        sys.stderr.write("\nk: " + k +" v: " + str(v))
        if k == "href":
           
            href_lst = v.split("/")
            sys.stderr.write("href_lst: %s" % (str(href_lst)))
            c_name = href_lst[-1]
            c_type = href_lst[-2]
            k_key = "{type}.{c_name}.{c_type}".format(type=obj_type, c_name=c_name, c_type=c_type)
            obj = {}
            p_query = 'search index={index_name} sourcetype="_json" earliest=0 name={name} device={device} domain={domain} type={type} '
            sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS p_query: {}!!\n".format(p_query))
            try:
                p_query = p_query.format(index_name=index_name, name=c_name, type=c_type, domain=obj_domain, device=obj_device)
            except Exception as ex:
                splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))                                    

            #c_res = es.search(index=index_name, body=c_mm)
            
            #time.sleep(0.005)

            c_res_lst = []
            savd_key = (obj_device, obj_domain, c_type, c_name)
            
            if savd_key in down_saved_resps:    
                sys.stderr.write("\n222 saved key known")
                c_res = down_saved_resps[savd_key]
                sys.stderr.write("c_res: %s" % (str(c_res)))
            else:
                kwargs_oneshot = { "count": 0 }
                sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS p_query222: {}!!\n".format(p_query))
                #c_response = service.jobs.oneshot(p_query, **kwargs_oneshot)
                #sys.stderr.write("\nIN after 222 1 c_response: %s" % str(c_response))
                c_res = None
                try:
                    c_res = splunklib.results.ResultsReader(service.jobs.oneshot(p_query, **kwargs_oneshot))
                except Exception as ex:
                    splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))                                    
    
                sys.stderr.write("\nIN after 222\n")
                
                sys.stderr.write("c_res: %s\n" % (str(c_res)))
                if c_res is not None:
                    sys.stderr.write("c_res not none: %s" % (str(c_res)))

                    for r in c_res:
                        sys.stderr.write("c_res not none looping!\n")
                        sys.stderr.write("r: %s\n" % (str(r)))
                        sys.stderr.write("r_raw: %s\n" % (str(r["_raw"])))
                        sys.stderr.write("r_raw_t: %s\n" % (str(type(r["_raw"]))))
                        sys.stderr.write("json.loads r_raw: %s\n" % (str(json.loads(r["_raw"]))))
                        c_res_lst.append(json.loads(r["_raw"]))
                        sys.stderr.write("\njson.loads r_raw after append\n")
                else:
                    obj[k_key] =  {"fail": "SEARCH FAILED!", "name": c_name, "type": c_type}  
                    #c["object"] = {"fail": "SEARCH FAILED!", "name": c_name, "type": c_type}
            sys.stderr.write("\nafter appendish\n c_res_lst: %s" % (str(c_res_lst)))
            sys.stderr.write("\nc_res_lst len: %i " % (len(c_res_lst)) )
            if len(c_res_lst) == 1:
                #print c_res["hits"]["hits"] 
                #obj[k_key] = c_res_lst[0][c_type]
                v = c_res_lst[0][c_type]
                for (o_k, o_v) in v.items():
                    if o_k == "href":
                        recurse_down(v,  obj_name, obj_type)
            else:
                if len(c_res_lst) > 1:

                    obj[k_key] = {
                        "fail": "MULTIPLE OBJECTS NOT FOUND!",
                        "objects": []
                    }

                    for hit in c_res_lst:
                        obj[k_key]["objects"].append(hit)

                else:
                    obj[k_key] = {"fail": "OBJECT NOT FOUND!", "name": c_name, "type": c_type}
          
    else:
        pass


obj_domain = None
obj_device = None
def recurse_up(obj):
    """
    recurse objects.  
        1.)  find all docs that have 'class'='type' and 'value'='name' and recurse their kids.
        2.)  return when no kids

    """
    sys.stderr.write("!!!!!!!!!!! recurse_up !!!!!!!!!!!!!!!1\n")
    global up_saved_resps
    global tops

    if "domain" in obj:
        if isinstance(obj["domain"], list):
            obj_domain = obj["domain"][0] 
        else:
            obj_domain = obj["domain"]    

    if "device" in obj:
        if isinstance(obj["device"], list):
            obj_device = obj["device"][0] 
        else:
            obj_device = obj["device"]    

    t = ""
    n = ""
    if "type" in obj:
        if isinstance(obj["type"], list):
            t = obj["type"][0]
        else:    
            t = obj["type"]

    if "name" in obj:
        if isinstance(obj["name"], list):
            n = obj["name"][0]
        else:    
            n = obj["name"]

    h_ref = "/mgmt/config/{domain}/{type}/{name}"
    if "type" in obj and "name" in obj:
        h_ref = "/mgmt/config/{domain}/{type}/{name}".format(domain=obj["domain"], type=t, name=n)

    sys.stderr.write("!!!!!!!!!!! before c_query !!!!!!!!!!!!!!!1\n")
    c_query = """
        search index={index_name} sourcetype="_json" earliest=0 device="{device}" domain="{domain}" "{search_term}" "{h_ref}" type!="DomainAvailability" 
    """.format(index_name=index_name,  search_term=n, search_class=t, domain=obj_domain, device=obj_device, h_ref=h_ref, name=n, type=t)
    #sys.stderr.write("c_query: " + c_query + "\n")
    #c_res = es.search(index=index_name, body=c_mm)
    kwargs_oneshot = { "count": 0 }
    #time.sleep(0.005)
    #sys.stderr.write("!!!!!!!!!!! AFTER c_query !!!!!!!!!!!!!!!1\n")                
    up_saved_resps_key = (obj_device, obj_domain, t, n)
    #sys.stderr.write("up_saved_resps HAS KEY: " + str(up_saved_resps.has_key(up_saved_resps_key)))
    c_res = None
    c_res_lst = []
    if up_saved_resps_key in up_saved_resps:
        #sys.stderr.write("up_saved_resps FOUND KEY!!")
        c_res_lst = up_saved_resps[up_saved_resps_key]
    else:
        response = service.jobs.oneshot(c_query, **kwargs_oneshot)
        c_res = splunklib.results.ResultsReader(response)
        #sys.stderr.write("AFTERsd up_saved_resps!! up_saved_resps:" + str(up_saved_resps))
        if c_res is not None:
            #sys.stderr.write("FIND TOPS c_res ok\n")

            for h in c_res:
                sys.stderr.write("H:<<<<<<<<{}>>>>>>>>>>".format(str(h)))
                #c_res_lst.append(eval(h["_raw"]))
                c_res_lst.append(eval(h["_raw"]))
            up_saved_resps[up_saved_resps_key] = c_res_lst
            #sys.stderr.write("FIND TOPS c_res_lst len: {}\n".format(len(c_res_lst)))

    if len(c_res_lst) > 0:
        
        for hit in c_res_lst:
            show_hits = True
            if "only_show_top_levels" in parm_dict:
                if parm_dict["only_show_top_levels"] == "true":
                    show_hits = False
            if "output_dependency_tree" in parm_dict:
                if parm_dict["output_dependency_tree"] == "true":
                    show_hits = False
            #print json.dumps(eval(str(hit["_source"])), indent=2)
            #sys.stderr.write("\nFIND TOPS SHOW HITS: {}!\n".format(show_hits))
            if show_hits:
                sys.stderr.write("\nFIND TOPS SHOW HITS TRUE!\n")
                #print "Recurse up hit! name: {} type: {}".format(hit["name"], hit["type"])
                #new_result = {}
                new_result = OrderedDict()
                t = ""
                n = ""
                if isinstance(hit["type"], list):
                    t = hit["type"][0]
                else:    
                    t = hit["type"]

                if isinstance(hit["name"], list):
                    n = hit["name"][0]
                else:    
                    n = hit["name"]

                new_result["device"] = hit["device"]
                new_result["domain"] = hit["domain"]
                new_result["type"] = t
                new_result["name"] = n
                
                # new_result["elements"] = hit["elements"]
                # new_result["attrib"] = hit["attrib"]
                #new_result["_raw"] = hit["raw"]
                if new_result not in new_results:
                    new_results.append(new_result)

            recurse_up(hit)
    else:
        #sys.stderr.write("\nELSE!! ADD TO TOPS!!! OBJ: {}\n".format(str(obj)))
        #tpl = (obj["type"], obj["name"])
        if obj not in tops:
            tops.append(obj)


def find_tops(in_obj):

    global up_saved_resps
    global tops
    #sys.stderr.write("!!!!!!!!!!!find_tops  !!!!!!!!!!!!!!!1\n")

    recurse_up(in_obj)

    #sys.stderr.write("!!!!!!!!!!!find_tops done !!!!!!!!!!!!!!!1\n")
    #sys.stderr.write("tops: {}\n".format(str(tops)))

    return 

def process_results(res):
    global new_results
    global tops

    if res is not None:
        #sys.stderr.write("\nFOLLOW RES!!\n")

        for hit in res:
            #print hit.keys()
            #print hit["_raw"]
            show_hits = True
            if "only_show_top_levels" in parm_dict:
                if parm_dict["only_show_top_levels"] == "true":
                    show_hits = False
                    sys.stderr.write("\n!!!!only_show_top_levels TRUE!!\n")
            if "output_dependency_tree" in parm_dict:
                if parm_dict["output_dependency_tree"] == "true":
                    show_hits = False
            #sys.stderr.write("\nSHOW HITS: {}!!\n".format(str(show_hits)))
            if show_hits:
                #sys.stderr.write("\nIN SHOW HITS before got hit print. hit: {} \n".format(str(hit)))
                #sys.stderr.write("Before try\n")    
                # try:
                #     #sys.stderr.write("Before print\n")
                #     #sys.stderr.write("Got hit! name: {} type: {} device: {} domain: {} \n".format(hit["name"], hit["type"], hit["device"], hit["domain"]))
                #     #sys.stderr.write("Got hit! name: {} type: {} device: {} domain: {} \n".format(hit["name"], hit["type"], hit["device"], hit["domain"]))
                #     #sys.stderr.write("After print\n")    
                # except Exception, ex:
                #     sys.stderr.write("In except.\n")
                #     sys.stderr.write("Exception!!!!  " + str(ex) + " " + str(type(ex)))
                #new_obj = {}
                # sys.stderr.write("Before dict create.\n")
                new_obj = OrderedDict()

                if "device" in hit:                
                    if isinstance(hit["device"], list):
                        new_obj["device"] = hit["device"][0]
                    else:    
                        new_obj["device"] = hit["device"]

                if "domain" in hit:                
                    if isinstance(hit["domain"], list):
                        new_obj["domain"] = hit["domain"][0]
                    else:    
                        new_obj["domain"] = hit["domain"]

                
                # new_obj["device"] = hit["device"]
                # new_obj["domain"] = hit["domain"]
                if "type" in hit:
                    if isinstance(hit["type"], list):
                        new_obj["type"] = hit["type"][0]
                    else:    
                        new_obj["type"] = hit["type"]

                if "name" in hit:
                    if isinstance(hit["name"], list):
                        new_obj["name"] = hit["name"][0]
                    else:    
                        new_obj["name"] = hit["name"]

                #new_obj["name"] = hit["name"]
                #new_obj["_raw"] = hit["_raw"]
                #new_obj["elements"] = hit["elements"]
                #new_obj["attrib"] = hit["attrib"]
                new_results.append(new_obj)

            #print json.dumps(eval(str(hit["_source"])), indent=2)
            #if args.follow_dependencies:
            if "follow_dependencies" in parm_dict:                        
                if parm_dict["follow_dependencies"] == "true":
                    #hit_doc = eval(hit["_raw"])
                    hit_doc = hit
                    sys.stderr.write("!!!!!!!!!!! BEFORE find_tops!!!!!!!!!!!!!!!1\n")                
                    find_tops(hit_doc)

        #sys.stderr.write("!!!!!!!!!!! BEFORE only_show_top_levels!!!!!!!!!!!!!!!1\n")                
        if "follow_dependencies" in parm_dict:
            if parm_dict["follow_dependencies"] == "true":                        
                top_levels = False
                #sys.stderr.write("!!!!!!!!!!!1only_show_top_levels!!!!!!!!!!!!!!!1\n")
                if "only_show_top_levels" in parm_dict:
                    if parm_dict["only_show_top_levels"] == "true":
                        top_levels = True
                    
                if "output_dependency_tree" in parm_dict:
                    if parm_dict["output_dependency_tree"] == "true":
                        top_levels = False
                
                if top_levels:
                    sys.stderr.write("Found {} top level documents".format(len(tops)))
                    tops_dict = {}
                    for t in tops:
                        #new_result = {}
                        new_result = OrderedDict()

                        if "device" in t:
                            if isinstance(t["device"], list):
                                new_result["device"] = t["device"][0]
                            else:    
                                new_result["device"] = t["device"]

                        if "domain" in t:
                            if isinstance(t["domain"], list):
                                new_result["domain"] = t["domain"][0]
                            else:    
                                new_result["domain"] = t["domain"]
                        # new_result["device"] = t["device"]
                        # new_result["domain"] = t["domain"]
                        if "type" in t:
                            if isinstance(t["type"], list):
                                new_result["type"] = t["type"][0]
                            else:    
                                new_result["type"] = t["type"]

                        if "name" in t:
                            if isinstance(t["name"], list):
                                new_result["name"] = t["name"][0]
                            else:    
                                new_result["name"] = t["name"]
                        # new_result["type"] = t["type"]
                        # new_result["name"] = t["name"]
                        
                    
                        #new_result["elements"] = t["elements"]
                        #new_result["attrib"] = t["attrib"]
                        #new_result["_raw"] = t["_raw"]
                        new_results.append(new_result)

                        tops_dict[t["type"]] = t["name"]
                    #sys.stderr.write("Top level documents: {} \n".format(str(tops_dict)))

                i = 1
                obj = {}

                if  "print_full_json_dependency_tree" in parm_dict or "print_text_dependency_tree" in parm_dict or "output_dependency_tree" in parm_dict:
                    for top in tops:
                        sys.stderr.write("\nFOR TOP IN TOPS&&&!! TOP: %s \n" % (str(top)))

                        if "only_show_top_levels" in parm_dict:
                            if parm_dict["only_show_top_levels"] == "true":
                                continue

                        # sys.stderr.write("\nBEFOR recurse_down&&&!!\n")
                        #obj_domain = None
                        #obj_device = None                            
                       
                        recurse_down(top)

                        # sys.stderr.write("\nAFTER recurse_down&&&!!\n")
                        if "print_full_json_dependency_tree" in parm_dict:
                            if parm_dict["print_full_json_dependency_tree"] == "true":
                                sys.stderr.write("-----------------{}.) {}: {} ------------------".format(i, top["type"], top["name"]))
                                sys.stderr.write((json.dumps(eval(str(top)), indent=2)))
                        

                        if "print_text_dependency_tree" in parm_dict:
                            if parm_dict["print_text_dependency_tree"] == "true":
                                indent_lvl = 0
                                def print_text_recurse(obj):
                                    #global indent_lvl
                                    #print "obj:", obj
                                    if obj["name"] == "PowerCurve":
                                        pass

                                    sys.stderr.write("{} {}: {}".format('|-' * indent_lvl, obj["type"], obj["name"]).lstrip())
                                

                                    for (k,v)  in obj.items():
                                        if k == "href":
                                            #print "e:", e
                                            #if "class" in e:
                                            indent_lvl = indent_lvl + 2
                                            print_text_recurse(obj)
                                            indent_lvl = indent_lvl - 2
                                    
                                print_text_recurse(top)

                        # sys.stderr.write("\nBEFPRE output_dependency_tree&&&!!\n")
                        if "output_dependency_tree" in parm_dict:
                            if parm_dict["output_dependency_tree"] == "true":
                                # sys.stderr.write("\nIN output_dependency_tree&&&!!\n")
                                #indent_lvl = 0
                                parent_lst = []
                                
                                def print_recurse(obj, in_parent):
                                    #global indent_lvl
                                    #global parent_lst
                                    parent = in_parent
                                    #print "obj:", obj
                                    # sys.stderr.write("\nIN print_recurse&&&!!\n")
                                    #print "{} {}: {}".format('|-' * indent_lvl, obj["type"], obj["name"]).lstrip()
                                    if in_parent != "1235":
                                    
                                    
                                        t = ""
                                        n = ""
                                        
                                        if isinstance(obj["type"], list):
                                            t = obj["type"][0]
                                        else:    
                                            t = obj["type"]

                                        if "name" in obj:
                                            if isinstance(obj["name"], list):
                                                n = obj["name"][0]
                                            else:    
                                                n = obj["name"]

                                        new_result = OrderedDict()
                                        new_result["parent"] = parent
                                        if n == "":
                                            new_result["name"] = "{}".format(n)
                                        else:
                                            new_result["name"] = "{}: {}".format(t, n)
                                        #new_result["name"] = "{}: {}".format(t, n)
                                        new_result["count"] = 1

                                        if new_result not in parent_lst:
                                            new_results.append(new_result)
                                            parent_lst.append(new_result)
                                    # sys.stderr.write("\nIN print_recurse after in_parent Top&&&!!\n")
                                    # sys.stderr.write("\nIN print_recurse obj IS!!! e: {}\n".format(str(obj)))
                                    if "elements" in obj:
                                        # sys.stderr.write("\nIN print_recurse obj has eleents!!\n")
                                        for e in obj["elements"]:
                                            #print "e:", e
                                            # sys.stderr.write("\nIN print_recurse e IS!!! e: {}\n".format(str(e)))
                                            # sys.stderr.write("\nIN print_recurse E has_key CLASS: {}\n".format(str(e.has_key("class"))))
                                            # sys.stderr.write("\nIN print_recurse E has_key object: {}\n".format(str(e.has_key("object"))))                                                
                                            if "object" in e:
                                                #indent_lvl = indent_lvl + 2
                                                #save_parent = parent
                                                t = ""
                                                n = ""
                                                # sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                                
                                                if "type" in obj:
                                                    if isinstance(obj["type"], list):
                                                        t = obj["type"][0]
                                                    else:    
                                                        t = obj["type"]

                                                if "name" in obj:
                                                    if isinstance(obj["name"], list):
                                                        n = obj["name"][0]
                                                    else:    
                                                        n = obj["name"]
                                                    
                                                # sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                                if n == "":
                                                    parent = "{}".format(n)
                                                else:
                                                    parent = "{}: {}".format(t, n)

                                                if "object" in e:
                                                    print_recurse(e["object"], parent)
                                                else:
                                                    #sys.stderr.write("\nIN print_recurse obj e has no object!!! e: {}\n".format(str(e)))
                                                    pass    
                                                #parent = save_parent
                                            else:
                                                if "elements" in e:
                                                    for ee in e["elements"]:
                                                        t = ""
                                                        n = ""
                                                        if "object" in ee:
                                                            #sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                                            
                                                            if "type" in obj:
                                                                if isinstance(obj["type"], list):
                                                                    t = obj["type"][0]
                                                                else:    
                                                                    t = obj["type"]

                                                            if "name" in obj:
                                                                if isinstance(obj["name"], list):
                                                                    n = obj["name"][0]
                                                                else:    
                                                                    n = obj["name"]
                                                                
                                                            #sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                                            if n == "":
                                                                parent = "{}".format(n)
                                                            else:
                                                                parent = "{}: {}".format(t, n)

                                                            print_recurse(ee["object"], parent)
                                    else:
                                        if "object" in obj:
                                            t = ""
                                            n = ""
                                            #sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                            if "type" in obj:                                            
                                                if isinstance(obj["type"], list):
                                                    t = obj["type"][0]
                                                else:    
                                                    t = obj["type"]

                                            if "name" in obj:
                                                if isinstance(obj["name"], list):
                                                    n = obj["name"][0]
                                                else:    
                                                    n = obj["name"]
                                                
                                            #sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                            if n == "":
                                                parent = "{}".format(n)
                                            else:
                                                parent = "{}: {}".format(t, n)
                                            print_recurse(obj["object"], parent)


                                #sys.stderr.write("\n BEFORE print_recurse!!\n")    
                                print_recurse(top, "Domain")

                        #print json.dumps(eval(str(obj)), indent=2)
                        #obj = recurse_up(hit["_source"])
                        #print json.dumps(eval(str(obj)), indent=2)
                        i = i + 1

    else:
        sys.stderr.write("Exception! Search failed? Result:" + str(res))
        splunk.Intersplunk.addErrorMessage(messages, "Exception! Search failed? Result:" + str(res))


try:

    # service = splunklib.client.connect(
    #     host=HOST,
    #     port=PORT,
    #     username=USERNAME,
    #     password=PASSWORD)

    service = splunklib.client.connect(token=s_token)

    if len(results) == 0:
        if "text" in parm_dict or "element_value" in parm_dict:
            query = ""
            domain_device_str = ""
            if "domain" in parm_dict:
                domain_device_str = domain_device_str + '"domain"="{}" '.format(parm_dict["domain"])
            if "device" in parm_dict:
                domain_device_str = domain_device_str + '"device"="{}" '.format(parm_dict["device"])

            if "text" in parm_dict:
                query = """search index={index_name} sourcetype="_json" earliest=0 {search_text} | spath | search {domain_device} name=* type=* """.format(index_name=index_name,  search_text=parm_dict["text"], domain_device=domain_device_str)
                if "element_type" in parm_dict:
                    query = """
                        search index={index_name} sourcetype="_json" earliest=0 {search_text} | spath | search {domain_device} "type"={element_type} OR "elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}
                        """.format(index_name=index_name, search_text=parm_dict["text"], element_type=parm_dict["element_type"], domain_device=domain_device_str)


                    if "object_type" in parm_dict:
                        query = """
                            search index={index_name} sourcetype="_json" earliest=0 {search_text} | spath | search {domain_device} ("type"={element_type} OR "elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) AND "type"={object_type}
                            """.format(index_name=index_name, search_text=parm_dict["text"], element_type=parm_dict["element_type"], object_type=parm_dict["object_type"], domain_device=domain_device_str)
                    
                else:
                    if "object_type" in parm_dict:
                        query = """search index={index_name} sourcetype="_json" earliest=0 {search_text} | spath | search {domain_device} "type"={object_type} """.format(index_name=index_name,  search_text=parm_dict["text"], object_type=parm_dict["object_type"], domain_device=domain_device_str)

            if "element_value" in parm_dict:
                query = """
                    search index={index_name} sourcetype="_json" earliest=0 {search_term} | spath | search {domain_device} "value"={search_term}  OR "elements{{}}.value"={search_term} OR "elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} 
                """.format(index_name=index_name,  search_term=parm_dict["element_value"], domain_device=domain_device_str)

                if "element_type" in parm_dict:
                    query = """
                        search index={index_name} sourcetype="_json" earliest=0 {search_term} | spath | search {domain_device} ("value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) 
                    """.format(index_name=index_name,  search_term=parm_dict["element_value"], element_type=parm_dict["element_type"], domain_device=domain_device_str)

                    if "object_type" in parm_dict:
                        query = """
                            search index={index_name} sourcetype="_json" earliest=0 {search_term} | spath | search {domain_device} "type"={object_type} ("value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) 
                        """.format(index_name=index_name,  search_term=parm_dict["element_value"], element_type=parm_dict["element_type"], object_type=parm_dict["object_type"], domain_device=domain_device_str)


                else:
                    if "object_type" in parm_dict:
                        query = """
                            search index={index_name} sourcetype="_json" earliest=0 {search_term} | spath | search {domain_device} "type"={object_type} "value"={search_term}  OR "elements{{}}.value"={search_term} OR "elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} 
                        """.format(index_name=index_name,  search_term=parm_dict["element_value"], object_type=parm_dict["object_type"], domain_device=domain_device_str)
                        

            if "verbose" in parm_dict:
                sys.stderr.write("Query: {}\n".format(query))    
                #print json.dumps(eval(str(mm)), indent=2)
                #print query

            #res = es.search(index=index_name, body=mm, size=9999)
            kwargs_oneshot = { "count": 0 }
            #time.sleep(0.005)
            response = service.jobs.oneshot(query, **kwargs_oneshot)
            res = splunklib.results.ResultsReader(response)

            process_results(res)
            #print res    
    else:
        process_results(results)

except Exception as ex:
    sys.stderr.write("Exception occurred. Exception:{}".format(str(ex)))
    splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))

splunk.Intersplunk.outputResults(new_results, messages=messages)
