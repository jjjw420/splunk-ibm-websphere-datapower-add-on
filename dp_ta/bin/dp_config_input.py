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
import lxml.etree
import json
import argparse
import tempfile
import os
import splunklib.client 
import splunklib.results
from collections import OrderedDict
import zipfile
import time
import sys
import glob
import shutil

HOST = "localhost"
PORT = 8089

index_name = "esb_dp_config"
domain = None
device = None

if __name__ == '__main__':

    # parser = argparse.ArgumentParser(description="Datapower Impact analysis tool. Splunk input.", formatter_class=argparse.RawDescriptionHelpFormatter)

    # parser.add_argument("-f", "--file", action="store", type=str, dest="file", help="The Datapower export.xml or export zip file to read. Will also check for embedded zip files.", default="/home/hannes/workspace/python/DPVisualizer/PROD/Prod/export.xml")
    
    # parser.add_argument("-c", "--clean_index", action="store_true", dest="clean_index", help="Clean the index. ", default=False)
    # parser.add_argument("-w", "--workfolder", action="store", type=str, dest="/tmp/dp_config_input", help="The default working folder.", default=None)
    
    # parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Verbose. ", default=False)

    # args = parser.parse_args()
    delete_index = True
    input_exports_folder = "/filexfer/splunk/esb/dp/config"

    try:


        session_key = sys.stdin.readline().strip()

        if len(session_key) == 0:
            sys.stderr.write("Did not receive a session key from splunkd. " +
                            "Please enable passAuth in inputs.conf for this " +
                            "script\n")
            sys.exit(2)

        sys.stdout.write("Got Session Key: " + session_key + "\n");
        sys.stdout.flush()

        # service = splunklib.client.connect(
        #     host=HOST,
        #     port=PORT,
        #     username=USERNAME,
        #     password=PASSWORD)

        service = splunklib.client.Service(token=session_key, host=HOST, port=PORT)

        index = None
        delete_index = False
        if len(glob.glob(os.path.join(input_exports_folder, "*.zip"))) > 0:
            delete_index = True
        else:
            sys.exit(0)
        if delete_index:

            try:
                index = service.indexes[index_name]
                index.clean()
                time.sleep(2)
            except KeyError:
                sys.stderr.write("Index %s not found on splunk. Creating...\n" % index_name)
                service.indexes.create(index_name)
                time.sleep(1)

        try:
            index = service.indexes[index_name]
        except KeyError:
            sys.stderr.write("Index %s not found on splunk. Create failed!.\n" % index_name)
            sys.exit(1) 

        stream = index.attach(source="dpconfig", sourcetype="_json")      
        stream_xml = index.attach(source="dpconfig", sourcetype="dpconfigxml")      

        def recurse(el, obj):
            #print el.tag, el.attrib, el.text

            obj["type"] = el.tag


            if len(el.attrib.keys()) > 0:
                obj["attrib"] = el.attrib
                if el.attrib.has_key("name"):
                    obj["name"] = el.attrib["name"]
                if el.attrib.has_key("class"):
                    obj["class"] = el.attrib["class"]

            if len(el) > 0:
                obj["elements"] = []
                for c in el:
                    #new_obj = {}
                    new_obj = OrderedDict()
                    obj["elements"].append(new_obj)
                    recurse(c, new_obj)

            if el.text is not None:
                if el.text.strip() != "":
                    obj["value"] = el.text
            else:
                return 


        def recurse_for_zips(zip_file_name):
            #sys.stderr.write("Reading zip file: {}\n".format(zip_file_name))
            zipf = zipfile.ZipFile(zip_file_name, 'r', zipfile.ZIP_DEFLATED)

            z_info_l = zipf.infolist()
            root = None
            #sys.stderr.write("b4 loop\n")
            for z_i in z_info_l:
                in_file_data = None
                if z_i.filename.count("export.xml") > 0:

                    in_file_data = zipf.read(z_i)
            
                    root = lxml.etree.fromstring(in_file_data)

                    #sys.stderr.write("Indexing Documents...\n")   
                    
                    nl = root.xpath("./export-details/domain")
                    if len(nl) == 0:
                        sys.stderr.write("Domain not found?\n")
                        continue
                    else:
                        domain = nl[0].text

                    nl = root.xpath("./export-details/device-name")
                    if len(nl) == 0:
                        sys.stderr.write("Device not found?\n")
                        continue
                    else:
                        device = nl[0].text

                    nl = root.xpath("./configuration")
                    if len(nl) == 0:
                        sys.stderr.write("No configuration tag found?\n")
                        continue

                    for c in nl[0]: 
                        #obj = {}
                        obj = OrderedDict()

                        obj_type = c.tag
                        obj_name = c.attrib["name"]
                        
                        recurse(c, obj)
                        
                        obj["device"] = device
                        obj["domain"] = domain
                        #print "------------------"

                        root_el = lxml.etree.Element("dpobject") 
                        device_el = lxml.etree.SubElement(root_el, "device")
                        device_el.text = device
                        domain_el = lxml.etree.SubElement(root_el, "domain")
                        domain_el.text = domain
                        type_el = lxml.etree.SubElement(root_el, "type")
                        type_el.text = obj_type
                        name_el = lxml.etree.SubElement(root_el, "name")
                        name_el.text = obj_name
                        object_el = lxml.etree.SubElement(root_el, "object")
                        object_el.append(c)

                        #res = es.index(index=index_name, doc_type='dpobj', body=eval(str(obj)))
                        if obj["type"] != "DomainAvailability" and obj["type"] != "Pattern":
                            body = json.dumps(eval(str(obj)))
                            stream.write(body + "\n")
                            body = "\n[NEWOBJECT]" + lxml.etree.tostring(root_el,pretty_print=True)
                            stream_xml.write(body)        
                        
                        # if args.verbose:
                        #     print(res)
                        #     print json.dumps(eval(str(obj)), indent=2)

                else:
                    if z_i.filename.endswith(".zip") and z_i.filename.count("Exemplar") == 0:
                        #sys.stderr.write("found zip {} in zip file {}".format(z_i.filename, zip_file_name))
                        tmp_folder = tempfile.mkdtemp(dir="/tmp")
                        #sys.stderr.write("extracting {} to  {}".format(z_i.filename, tmp_folder))
                        zipf.extract(z_i, tmp_folder)

                        recurse_for_zips(os.path.join(tmp_folder, z_i.filename))
                        #sys.stderr.write("deleting tmp folder {}.".format(tmp_folder))
                        shutil.rmtree(tmp_folder)
                    
        for fle in glob.glob(os.path.join(input_exports_folder, "*.zip")):
            recurse_for_zips(fle)
            #sys.stderr.write("Deleting input:{} \n".format(str(fle)))    
            os.remove(fle)

    except Exception, ex:
        #print "Exception occurred. Exception:{}".format(str(ex))
        sys.stderr.write("Exception occurred. Exception:{} \n".format(str(ex)))


