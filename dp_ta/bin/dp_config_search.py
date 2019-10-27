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
import splunk.Intersplunk
import splunklib.client 
import splunklib.results
import sys
from collections import OrderedDict


index_name="esb_dp_config"             

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
def recurse_down(obj):
    global obj_domain
    global obj_device
    global down_saved_resps
    #sys.stderr.write("\nIN recurse_down&&&!!\n")
    if obj.has_key("domain"):
        obj_domain = obj["domain"]
    if obj.has_key("device"):
        obj_device = obj["device"]
    if obj.has_key("elements"):
        #sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS&&&!!\n")

        for c in obj["elements"]:
            #sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS&&&!! c: {}\n".format(str(c)))
            if c.has_key("class"):
                #b_query = """search index={index_name} {name} | spath | search "device"="{device}" "domain"="{domain}" "name"="{name}" "type"="{type}" """
                #sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS c_query: {}}!!\n".format(b_query))
                #sys.stderr.write("\nIN recurse_down BEFORE p_query\n")
                p_query = 'search index={index_name} sourcetype="_json" earliest=1 {name} | spath | search "device"="{device}" "domain"="{domain}" "name"="{name}" "type"="{type}"'
                #sys.stderr.write("\nIN recurse_down obj HAS ELEMENTS c_query: {}!!\n".format(p_query))
                try:
                    p_query = p_query.format(index_name=index_name, name=c["value"], type=c["class"], domain=obj_domain, device=obj_device)
                except Exception, ex:
                    splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))                                    

                #c_res = es.search(index=index_name, body=c_mm)
                
                #time.sleep(0.005)

                c_res_lst = []
                savd_key = (obj_device, obj_domain, c["class"], c["value"])
                
                if down_saved_resps.has_key(savd_key):
                    c_res = down_saved_resps[savd_key]
                else:
                    kwargs_oneshot = { "count": 0 }
                    c_response = service.jobs.oneshot(p_query, **kwargs_oneshot)
                    c_res = splunklib.results.ResultsReader(c_response)
                    if c_res:
                        for r in c_res:
                            c_res_lst.append(r["_raw"])
                    else:
                        c["object"] = {"fail": "SEARCH FAILED!", "name": c["value"], "type": c["class"]}

                if len(c_res_lst) == 1:
                    #print c_res["hits"]["hits"] 
                    c["object"] = eval(c_res_lst[0])
                    if c["object"].has_key("elements"):
                        recurse_down(c["object"])
                else:
                    if len(c_res_lst) > 1:

                        c["object"] = {
                            "fail": "MULTIPLE OBJECTS NOT FOUND!",
                            "objects": []
                        }

                        for hit in c_res_lst:
                            c["object"]["objects"].append(eval(hit))

                    else:
                        c["object"] = {"fail": "OBJECT NOT FOUND!", "name": c["value"], "type": c["class"]}

            if c.has_key("elements"):
                recurse_down(c)            
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
    global up_saved_resps
    global tops

    if obj.has_key("domain"):
        if isinstance(obj["domain"], list):
            obj_domain = obj["domain"][0] 
        else:
            obj_domain = obj["domain"]    

    if obj.has_key("device"):
        if isinstance(obj["device"], list):
            obj_device = obj["device"][0] 
        else:
            obj_device = obj["device"]    

    c_query = """
        search index={index_name} sourcetype="_json" earliest=1 {search_term} | spath | search "domain"="{domain}" "device"="{device}" "type"!="DomainAvailability" (
        ("value"="{search_term}" AND "class"="{search_class}") OR 
        ("elements{{}}.value"="{search_term}" AND "elements{{}}.class"="{search_class}") OR 
        ("elements{{}}.elements{{}}.value"="{search_term}" AND "elements{{}}.elements{{}}.class"="{search_class}") OR 
        ("elements{{}}.elements{{}}.elements{{}}.value"="{search_term}" AND "elements{{}}.elements{{}}.elements{{}}.class"="{search_class}") OR 
        ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"="{search_term}" AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.class"="{search_class}") OR 
        ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"="{search_term}" AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.class"="{search_class}")
        ) 
    """.format(index_name=index_name,  search_term=obj["name"], search_class=obj["type"], domain=obj_domain, device=obj_device)
    
    #c_res = es.search(index=index_name, body=c_mm)
    kwargs_oneshot = { "count": 0 }
    #time.sleep(0.005)
    t = ""
    n = ""
    if obj.has_key("type"):
        if isinstance(obj["type"], list):
            t = obj["type"][0]
        else:    
            t = obj["type"]

    if obj.has_key("name"):
        if isinstance(obj["name"], list):
            n = obj["name"][0]
        else:    
            n = obj["name"]

    up_saved_resps_key = (obj_device, obj_domain, t, n)
    #sys.stderr.write("up_saved_resps HAS KEY: " + str(up_saved_resps.has_key(up_saved_resps_key)))
    c_res = None
    c_res_lst = []
    if up_saved_resps.has_key(up_saved_resps_key):
        #sys.stderr.write("up_saved_resps FOUND KEY!!")
        c_res_lst = up_saved_resps[up_saved_resps_key]
    else:
        response = service.jobs.oneshot(c_query, **kwargs_oneshot)
        c_res = splunklib.results.ResultsReader(response)
        #sys.stderr.write("AFTER up_saved_resps!! up_saved_resps:" + str(up_saved_resps))
        if c_res:
            #sys.stderr.write("FIND TOPS c_res ok\n")

            for h in c_res:
                #print "H:<<<<<<<<{}>>>>>>>>>>".format(str(h["_raw"]))
                c_res_lst.append(eval(h["_raw"]))
            up_saved_resps[up_saved_resps_key] = c_res_lst
            #sys.stderr.write("FIND TOPS c_res_lst len: {}\n".format(len(c_res_lst)))

    if len(c_res_lst) > 0:
        
        for hit in c_res_lst:
            show_hits = True
            if parm_dict.has_key("only_show_top_levels"):
                if parm_dict["only_show_top_levels"] == "true":
                    show_hits = False
            if parm_dict.has_key("output_dependency_tree"):
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
            if parm_dict.has_key("only_show_top_levels"):
                if parm_dict["only_show_top_levels"] == "true":
                    show_hits = False
                    sys.stderr.write("\n!!!!only_show_top_levels TRUE!!\n")
            if parm_dict.has_key("output_dependency_tree"):
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

                if hit.has_key("device"):                
                    if isinstance(hit["device"], list):
                        new_obj["device"] = hit["device"][0]
                    else:    
                        new_obj["device"] = hit["device"]

                if hit.has_key("domain"):                
                    if isinstance(hit["domain"], list):
                        new_obj["domain"] = hit["domain"][0]
                    else:    
                        new_obj["domain"] = hit["domain"]

                
                # new_obj["device"] = hit["device"]
                # new_obj["domain"] = hit["domain"]
                if hit.has_key("type"):
                    if isinstance(hit["type"], list):
                        new_obj["type"] = hit["type"][0]
                    else:    
                        new_obj["type"] = hit["type"]

                if hit.has_key("name"):
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
            if parm_dict.has_key("follow_dependencies"):                        
                if parm_dict["follow_dependencies"] == "true":
                    hit_doc = eval(hit["_raw"])
                    find_tops(hit_doc)

        # sys.stderr.write("!!!!!!!!!!! BEFORE only_show_top_levels!!!!!!!!!!!!!!!1\n")                
        if parm_dict.has_key("follow_dependencies"):
            if parm_dict["follow_dependencies"] == "true":                        
                top_levels = False
                # sys.stderr.write("!!!!!!!!!!!1only_show_top_levels!!!!!!!!!!!!!!!1\n")
                if parm_dict.has_key("only_show_top_levels"):
                    if parm_dict["only_show_top_levels"] == "true":
                        top_levels = True
                    
                if parm_dict.has_key("output_dependency_tree"):
                    if parm_dict["output_dependency_tree"] == "true":
                        top_levels = False
                
                if top_levels:
                    # sys.stderr.write("Found {} top level documents".format(len(tops)))
                    tops_dict = {}
                    for t in tops:
                        #new_result = {}
                        new_result = OrderedDict()

                        if t.has_key("device"):
                            if isinstance(t["device"], list):
                                new_result["device"] = t["device"][0]
                            else:    
                                new_result["device"] = t["device"]

                        if t.has_key("domain"):
                            if isinstance(t["domain"], list):
                                new_result["domain"] = t["domain"][0]
                            else:    
                                new_result["domain"] = t["domain"]
                        # new_result["device"] = t["device"]
                        # new_result["domain"] = t["domain"]
                        if t.has_key("type"):
                            if isinstance(t["type"], list):
                                new_result["type"] = t["type"][0]
                            else:    
                                new_result["type"] = t["type"]

                        if t.has_key("name"):
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
                    # sys.stderr.write("Top level documents: {} \n".format(str(tops_dict)))

                i = 1
                obj = {}

                if  parm_dict.has_key("print_full_json_dependency_tree") or parm_dict.has_key("print_text_dependency_tree") or parm_dict.has_key("output_dependency_tree"):
                    for top in tops:
                        # sys.stderr.write("\nFOR TOP IN TOPS&&&!!\n")
                        if parm_dict.has_key("only_show_top_levels"):
                            if parm_dict["only_show_top_levels"] == "true":
                                continue

                        # sys.stderr.write("\nBEFOR recurse_down&&&!!\n")
                        obj_domain = None
                        obj_device = None                            
                        recurse_down(top)
                        # sys.stderr.write("\nAFTER recurse_down&&&!!\n")
                        if parm_dict.has_key("print_full_json_dependency_tree"):
                            if parm_dict["print_full_json_dependency_tree"] == "true":
                                if args.print_full_json_dependency_tree:
                                    print "-----------------{}.) {}: {} ------------------".format(i, top["type"], top["name"])
                                    print json.dumps(eval(str(top)), indent=2)
                        

                        if parm_dict.has_key("print_text_dependency_tree"):
                            if parm_dict["print_text_dependency_tree"] == "true":
                                indent_lvl = 0
                                def print_recurse(obj):
                                    #global indent_lvl
                                    #print "obj:", obj
                                    if obj["name"] == "PowerCurve":
                                        pass
                                    print "{} {}: {}".format('|-' * indent_lvl, obj["type"], obj["name"]).lstrip()
                                

                                    if obj.has_key("elements"):
                                        for e in obj["elements"]:
                                            #print "e:", e
                                            if e.has_key("class"):
                                                indent_lvl = indent_lvl + 2
                                                print_recurse(e["object"])
                                                indent_lvl = indent_lvl - 2
                                    
                                print_recurse(top)

                        # sys.stderr.write("\nBEFPRE output_dependency_tree&&&!!\n")
                        if parm_dict.has_key("output_dependency_tree"):
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

                                        if obj.has_key("name"):
                                            if isinstance(obj["name"], list):
                                                n = obj["name"][0]
                                            else:    
                                                n = obj["name"]

                                        new_result = OrderedDict()
                                        new_result["parent"] = parent
                                        if n == "":
                                            new_result["name"] = "{}".format(t, n)
                                        else:
                                            new_result["name"] = "{}: {}".format(t, n)
                                        #new_result["name"] = "{}: {}".format(t, n)
                                        new_result["count"] = 1

                                        if new_result not in parent_lst:
                                            new_results.append(new_result)
                                            parent_lst.append(new_result)
                                    # sys.stderr.write("\nIN print_recurse after in_parent Top&&&!!\n")
                                    # sys.stderr.write("\nIN print_recurse obj IS!!! e: {}\n".format(str(obj)))
                                    if obj.has_key("elements"):
                                        # sys.stderr.write("\nIN print_recurse obj has eleents!!\n")
                                        for e in obj["elements"]:
                                            #print "e:", e
                                            # sys.stderr.write("\nIN print_recurse e IS!!! e: {}\n".format(str(e)))
                                            # sys.stderr.write("\nIN print_recurse E has_key CLASS: {}\n".format(str(e.has_key("class"))))
                                            # sys.stderr.write("\nIN print_recurse E has_key object: {}\n".format(str(e.has_key("object"))))                                                
                                            if e.has_key("object"):
                                                #indent_lvl = indent_lvl + 2
                                                #save_parent = parent
                                                t = ""
                                                n = ""
                                                # sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                                
                                                if obj.has_key("type"):
                                                    if isinstance(obj["type"], list):
                                                        t = obj["type"][0]
                                                    else:    
                                                        t = obj["type"]

                                                if obj.has_key("name"):
                                                    if isinstance(obj["name"], list):
                                                        n = obj["name"][0]
                                                    else:    
                                                        n = obj["name"]
                                                    
                                                # sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                                if n == "":
                                                    parent = "{}".format(t, n)
                                                else:
                                                    parent = "{}: {}".format(t, n)

                                                if e.has_key("object"):
                                                    print_recurse(e["object"], parent)
                                                else:
                                                    #sys.stderr.write("\nIN print_recurse obj e has no object!!! e: {}\n".format(str(e)))
                                                    pass    
                                                #parent = save_parent
                                            else:
                                                if e.has_key("elements"):
                                                    for ee in e["elements"]:
                                                        t = ""
                                                        n = ""
                                                        if ee.has_key("object"):
                                                            #sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                                            
                                                            if obj.has_key("type"):
                                                                if isinstance(obj["type"], list):
                                                                    t = obj["type"][0]
                                                                else:    
                                                                    t = obj["type"]

                                                            if obj.has_key("name"):
                                                                if isinstance(obj["name"], list):
                                                                    n = obj["name"][0]
                                                                else:    
                                                                    n = obj["name"]
                                                                
                                                            #sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                                            if n == "":
                                                                parent = "{}".format(t, n)
                                                            else:
                                                                parent = "{}: {}".format(t, n)

                                                            print_recurse(ee["object"], parent)
                                    else:
                                        if obj.has_key("object"):
                                            t = ""
                                            n = ""
                                            #sys.stderr.write("\nIN print_recurse IN E has_key CLASS: {}\n".format(""))
                                            if obj.has_key("type"):                                            
                                                if isinstance(obj["type"], list):
                                                    t = obj["type"][0]
                                                else:    
                                                    t = obj["type"]

                                            if obj.has_key("name"):
                                                if isinstance(obj["name"], list):
                                                    n = obj["name"][0]
                                                else:    
                                                    n = obj["name"]
                                                
                                            #sys.stderr.write("\nIN print_recurse E AFTER ISINSTANCE {}\n".format(""))
                                            if n == "":
                                                parent = "{}".format(t, n)
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
        sys.stderr.write("Exception! Search failed? Result:" + str(in_results))
        splunk.Intersplunk.addErrorMessage(messages, "Exception! Search failed? Result:" + str(in_results))


try:

    # service = splunklib.client.connect(
    #     host=HOST,
    #     port=PORT,
    #     username=USERNAME,
    #     password=PASSWORD)

    service = splunklib.client.connect(token=s_token)

    if len(results) == 0:
        if parm_dict.has_key("text") or parm_dict.has_key("element_value"):
            query = ""
            domain_device_str = ""
            if parm_dict.has_key("domain"):
                domain_device_str = domain_device_str + '"domain"="{}" '.format(parm_dict["domain"])
            if parm_dict.has_key("device"):
                domain_device_str = domain_device_str + '"device"="{}" '.format(parm_dict["device"])

            if parm_dict.has_key("text"):
                query = """search index={index_name} sourcetype="_json" earliest=1 {search_text} | spath | search {domain_device} name=* type=* """.format(index_name=index_name,  search_text=parm_dict["text"], domain_device=domain_device_str)
                if parm_dict.has_key("element_type"):
                    query = """
                        search index={index_name} sourcetype="_json" earliest=1 {search_text} | spath | search {domain_device} "type"={element_type} OR "elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}
                        """.format(index_name=index_name, search_text=parm_dict["text"], element_type=parm_dict["element_type"], domain_device=domain_device_str)


                    if parm_dict.has_key("object_type"):
                        query = """
                            search index={index_name} sourcetype="_json" earliest=1 {search_text} | spath | search {domain_device} ("type"={element_type} OR "elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) AND "type"={object_type}
                            """.format(index_name=index_name, search_text=parm_dict["text"], element_type=parm_dict["element_type"], object_type=parm_dict["object_type"], domain_device=domain_device_str)
                    

                else:
                    if parm_dict.has_key("object_type"):
                        query = """search index={index_name} sourcetype="_json" earliest=1 {search_text} | spath | search {domain_device} "type"={object_type} """.format(index_name=index_name,  search_text=parm_dict["text"], object_type=parm_dict["object_type"], domain_device=domain_device_str)

            if parm_dict.has_key("element_value"):
                query = """
                    search index={index_name} sourcetype="_json" earliest=1 {search_term} | spath | search {domain_device} "value"={search_term}  OR "elements{{}}.value"={search_term} OR "elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} 
                """.format(index_name=index_name,  search_term=parm_dict["element_value"], domain_device=domain_device_str)

                if parm_dict.has_key("element_type"):
                    query = """
                        search index={index_name} sourcetype="_json" earliest=1 {search_term} | spath | search {domain_device} ("value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) 
                    """.format(index_name=index_name,  search_term=parm_dict["element_value"], element_type=parm_dict["element_type"], domain_device=domain_device_str)

                    if parm_dict.has_key("object_type"):
                        query = """
                            search index={index_name} sourcetype="_json" earliest=1 {search_term} | spath | search {domain_device} "type"={object_type} ("value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "type"={element_type}) OR ("elements{{}}.value"={search_term} AND "elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) OR ("elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} AND "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.type"={element_type}) 
                        """.format(index_name=index_name,  search_term=parm_dict["element_value"], element_type=parm_dict["element_type"], object_type=parm_dict["object_type"], domain_device=domain_device_str)


                else:
                    if parm_dict.has_key("object_type"):
                        query = """
                            search index={index_name} sourcetype="_json" earliest=1 {search_term} | spath | search {domain_device} "type"={object_type} "value"={search_term}  OR "elements{{}}.value"={search_term} OR "elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} OR "elements{{}}.elements{{}}.elements{{}}.elements{{}}.elements{{}}.value"={search_term} 
                        """.format(index_name=index_name,  search_term=parm_dict["element_value"], object_type=parm_dict["object_type"], domain_device=domain_device_str)
                        

            if parm_dict.has_key("verbose"):
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

except Exception, ex:
    sys.stderr.write("Exception occurred. Exception:{}".format(str(ex)))
    splunk.Intersplunk.addErrorMessage(messages, "Exception occurred. Exception:{}".format(str(ex)))

splunk.Intersplunk.outputResults(new_results, messages=messages)
