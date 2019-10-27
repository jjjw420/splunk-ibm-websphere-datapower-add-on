#!/opt/splunk/bin/python

import sys
import csv
import splunk.Intersplunk
import string
import os
import zlib
import base64
import binascii
import uuid

try:
    import pymongo
    import bson.objectid
except:
    pass

MONGODB_HOST = "127.0.0.1"
MONGODB_PORT = 27018
MONGODB_DB_NAME = "dpwsm"
MONGODB_USER = "splunk"
MONGODB_PASSWORD = "splunk"
MONGODB_AUTH_DB = "admin"
MONGODB_USE_AUTH = False

(isgetinfo, sys.argv) = splunk.Intersplunk.isGetInfo(sys.argv)

#sys.stderr.write("isgetinfo:" + str(isgetinfo) + "\n")

if isgetinfo:
    splunk.Intersplunk.outputInfo(True, False, True, False, None, True)

if len(sys.argv) > 5:
    splunk.Intersplunk.parseError("Too many arguments provided.")

valid_parms = [""]

i = 1
parm_dict = {}
while i < len(sys.argv):
    arg = sys.argv[i]

#     if arg.count("=") == 1:
#         (parm, value) = arg.split("=")
#         if parm not in valid_parms:
#             splunk.Intersplunk.parseError("Invalid argument. Valid options are includeblob/dontfixpdgheader/extractblob/excludepayload/convertblob=<true|false> bloblimit/extractbloblimit=<integer>")
# #
# #         if parm == "bloblimit" or parm == "extractbloblimit":
# #             try:
# #                 int(value.strip())
# #             except:
# #                 splunk.Intersplunk.parseError("Invalid argument vale for bloblimit or extractbloblimit.  Must be an integer value.")
# #
# #         if parm == "includeblob" or parm == "dontfixpdgheader" or parm == "extractblob" or parm == "excludepayload" or parm == "convertblob":
# #             if value.strip().lower() != "true" and value.strip().lower() != "false":
# #                 splunk.Intersplunk.parseError("Invalid argument value for includeblob, extractblob or dontfixpdg.  Must be either true or false")
#
#         parm_dict[parm] = value
#
#     else:
#         if arg.count("=") > 1 or arg.count("=") <= 0:
#             splunk.Intersplunk.parseError("Invalid argument. Valid options are includeblob/dontfixpdgheader/extractblob/excludepayload/convertblob=<true|false> bloblimit/extractbloblimit=<integer>")

    i = i + 1
    # outputInfo automatically calls sys.exit()



def isPrintable(char):
    '''Return true if the character char is printable or false if it is not printable.
    '''
    if string.printable.count(char) > 0:
        return True
    else:
        return False

def makePrintable(instr):
    '''Return a printable representation of the string instr.
    '''
    retstr = ''
    for char in instr:
        if not isPrintable(char):
            retstr = retstr + '.'
        else:
            retstr = retstr + char
    return retstr

def get_msg_from_mongodb(mongodb_db, mongodb_collection, msg_id):

    if mongodb_db is None:
        #sys.stderr.write("Mongodb db none?")
        return None

    if msg_id is None:
        return None
    else:
        if len(msg_id) != 24:
            #splunk.Intersplunk.addWarnMessage(messages, "Msg id not 24 bytes?: %s" % (str(msg_id)))
            return None

    try:

        msg_doc = mongodb_db[mongodb_collection].find_one({"_id": bson.objectid.ObjectId(msg_id)})

        if msg_doc is not None:
            msg_data = msg_doc["payload"]

            uncomp_msg_data = zlib.decompress(base64.decodestring(msg_data), -15)
            return uncomp_msg_data

    except Exception, ex:
        sys.stderr.write("Exception while fetching message. Exception: %s\n" % (str(ex)))
        #splunk.Intersplunk.addMessage(messages, "Exception while fetching message from mongodb message. Exception: %s" % (str(ex)))
        pass

    return None

def get_msg_from_disk(domain, tid, msg_id, msg_folder):

    try:
        msg_file_name = os.path.join(msg_folder, domai, "%s_%s.dat" % (tid, msg_id))

        if os.path.exists(msg_file_name):
            msg_file_data = open(msg_file_name, "rb")
            msg_data = msg_file.read()
            msg_file.close()

            uncomp_msg_data = zlib.decompress(base64.decodestring(msg_data))
            return uncomp_msg_data

    except Exception, ex:
        splunk.Intersplunk.addErrorMessage(messages, "Exception while fetching message. Exception: %s" % (str(ex)))

    return None

results = splunk.Intersplunk.readResults(None, None, True)
#sys.stderr.write("Results!" + str(results[0].keys()) + "\n")
messages = {}

mongodb_client = None
mongodb_db = None
#splunk.Intersplunk.addInfoMessage(messages, "HJere")

for res in results:

    try:

        msg_folder = None
        if res.has_key("msg_folder"):
            msg_folder = res["msg_folder"]

        use_mongodb = False
        mongodb_collection = None
        if res.has_key("collection"):
            use_mongodb = True
            mongodb_collection = res["collection"]

        request_message_key = None
        response_message_key = None
        be_request_message_key = None
        be_response_message_key = None

        #sys.stderr.write("Starting...\n")
        domain = None
        if res.has_key("domain"):
            domain = res["domain"]
        else:
            splunk.Intersplunk.addWarnMessage(messages, "Event has no domain?")

        tid = None
        if res.has_key("transaction_id"):
            tid = res["transaction_id"]
        else:
            splunk.Intersplunk.addWarnMessage(messages, "Event has no transaction_id?")

        if res.has_key("request_message"):
            request_message_key = res["request_message"]
            #sys.stderr.write("request_message_key!" + request_message_key + "\n")

        if res.has_key("response_message"):
            response_message_key = res["response_message"]

        if res.has_key("be_request_message"):
            be_request_message_key = res["be_request_message"]

        if res.has_key("be_response_message"):
            be_response_message_key = res["be_response_message"]

        if use_mongodb:

            try:
                if mongodb_client is None:
                    mongodb_client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
                    mongodb_db = mongodb_client[MONGODB_DB_NAME]
                    if MONGODB_USE_AUTH:
                        mongodb_db.authenticate(MONGODB_USER, MONGODB_PASSWORD, source=MONGODB_AUTH_DB)

                if request_message_key is not None:
                    request_message_data = get_msg_from_mongodb(mongodb_db, mongodb_collection, request_message_key)

                    #sys.stderr.write("request_message_data!" + str(request_message_data)[0:20] + "\n")

                    if request_message_data is not None:
                        res["request_message_id"] = res["request_message"]
                        res["request_message"] = request_message_data

                        #res["request_message_data"] = request_message_data

                if response_message_key is not None:
                    response_message_data = get_msg_from_mongodb(mongodb_db, mongodb_collection, response_message_key)
                    #sys.stderr.write("response_message_data!" + str(response_message_data)[0:20] + "\n")
                    if response_message_data is not None:
                        res["response_message_id"] = res["response_message"]
                        res["response_message"] = response_message_data

                if be_request_message_key is not None:
                    be_request_message_data = get_msg_from_mongodb(mongodb_db, mongodb_collection, be_request_message_key)
                    #sys.stderr.write("be_request_message_data!" + str(be_request_message_data)[0:20] + "\n")

                    if be_request_message_data is not None:
                        res["be_request_message_id"] = res["be_request_message"]
                        res["be_request_message"] = be_request_message_data

                if be_response_message_key is not None:
                    be_response_message_data = get_msg_from_mongodb(mongodb_db, mongodb_collection, be_response_message_key)
                    #sys.stderr.write("be_response_message_data!" + str(be_response_message_data)[0:20] + "\n")

                    if be_response_message_data is not None:
                        res["be_response_message_id"] = res["be_response_message"]
                        res["be_response_message"] = be_response_message_data


            except Exception, ex:
                splunk.Intersplunk.addErrorMessage(messages, "MongoDB Exception occurred.  Exception:" + str(ex))

        else:
            if domain is not None and tid is not None:
                #on file system as files...
                if request_message_key is not None:
                    request_message_data = get_msg_from_disk(domain, tid, request_message_key, msg_folder)

                    if request_message_data is not None:
                        res["request_message_id"] = res["request_message"]
                        res["request_message"] = request_message_data

                if response_message_key is not None:
                    response_message_data = get_msg_from_disk(domain, tid, response_message_key, msg_folder)

                    if response_message_data is not None:
                        res["response_message_id"] = res["response_message"]
                        res["response_message"] = response_message_data

                if be_request_message_key is not None:
                    be_request_message_data = get_msg_from_disk(domain, tid, be_request_message_key, msg_folder)

                    if be_request_message_data is not None:
                        res["be_request_message_id"] = res["be_request_message"]
                        res["be_request_message"] = be_request_message_data

                if be_response_message_key is not None:
                    be_response_message_data = get_msg_from_disk(domain, tid, be_response_message_key, msg_folder)

                    if be_response_message_data is not None:
                        res["be_response_message_id"] = res["be_response_message"]
                        res["be_response_message"] = be_response_message_data
            else:
                #splunk.Intersplunk.addWarnMessage(messages, "Event payloads on disk but no domain or transaction_id in event.")
                pass

    except Exception, ex:
        splunk.Intersplunk.addErrorMessage(messages, "Exception occurred.  " + str(ex))


if mongodb_client is not None:
    try:
        mongodb_client.close()
    except:
        pass

splunk.Intersplunk.outputResults(results, messages=messages)
