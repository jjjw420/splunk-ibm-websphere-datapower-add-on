import random
import binascii
import string
import zlib
import cherrypy
import lxml.etree
import base64
import pymongo
import bson
import time
import datetime
import calendar
import json
import uuid
import zipfile
import os
import gzip


MONGODB_HOST = "127.0.0.1"
#MONGODB_HOST = "10.4.145.187"
MONGODB_PORT = 27017
MONGODB_DB_NAME = "dptrans"
MONGODB_USER = "splunk"
MONGODB_PASSWORD = "splunk"
MONGODB_AUTH_DB = "admin"
MONGODB_USE_AUTH = False


mongodb_client = pymongo.MongoClient(MONGODB_HOST, MONGODB_PORT)
mongodb_db = mongodb_client[MONGODB_DB_NAME]

if MONGODB_USE_AUTH:
    mongodb_db.authenticate(MONGODB_USER, MONGODB_PASSWORD,  source=MONGODB_AUTH_DB)

dev_devices = ["esbdpd01", "esbedpu01"]
sit1_devices = ["esbdpu01", "esbdpu02", "esbedpu01"]
sit2_devices = ["esbdps01", "esbdps02", "esbedpu01"]
prod_devices = ["esbdpp01", "esbdpp02", "esbdpp03", "esbdpp04", "esbdpp06", "esbdpp08", "esbedpp01", "esbedpp02", "esbedpp03", "esbedpp04"]


class WSMPayloadServer(object):
    exposed = True


    @cherrypy.expose
    def index(self):
        print mongodb_db.collection_names()
        help_text = """
            Available Operations:
                getwsmevent:  Fetches a WSM event payload based on it's collection and id.
                    Parms: collection - required
                           id - required

                getwsmeventdoc: Fetches a WSM event document based on it's collection and id.
                    Parms: collection - required
                           id - required

                getwsmeventdoclist:  fetches and list of event documents based on passed parameters.
                    Parms: collection - required
                           starttime - required (format YYYYmmddHHMMSS)
                           endtime - required (format YYYYmmddHHMMSS)
                           device - optional
                           domain - optional
                           service - optional
                           status - optional
                           tid - optional
                           payload - optional
                           uncompress - optional
                           downloadaszip - optional

                    eg. http://host:25015/getwsmeventdoclist?collection=20160901.TestSplunk&starttime=20160831075600&endtime=20160901231400&device=localdp&service=TestMPG&operation=TestMPG&downloadaszip=yesplease

                getcollections: Fetches the list of database collections based on passed paramters.
                    Parms:  domain - optional
                            capturedate - optional

                downloadwsmevents:  downloads payloads from a collection.
                    Parms:  collection - required
                            starttime - optional (format YYYYmmddHHMMSS)
                            endtime - optional (format YYYYmmddHHMMSS)
                            device - optional
                            service - optional
                            payload - optional (make sure it's url encoded in need be)

                    eg. http://127.0.0.1:25015/downloadwsmevents?collection=20160903.TestSplunk&service=TestMPG&starttime=20160903015100&endtime=2016090302000
                        http://127.0.0.1:25015/downloadwsmevents?collection=20160903.TestSplunk

                downloadwsmeventsbypayload:  downloads all payloads which match a particular string accross all collections for a particular date.
                    Parms:  date - required (format YYYYmmdd)
                            environment - required (dev1, sit1, sit2)
                            payload - required (the text to look for in the payload - i.e. traceid - make sure it's url encoded if need be)
                            starttime - optional (format YYYYmmddHHMMSS)
                            endtime - optional (format YYYYmmddHHMMSS)
                            device - optional
                            service - optional


                    eg. http://127.0.0.1:25015/downloadwsmeventsbypayload?date=20160903&environment=dev1&starttime=20160903015100&endtime=2016090302000
                        http://127.0.0.1:25015/downloadwsmeventsbypayload?date=20160903&environment=sit1


        """
        cherrypy.response.headers['Content-type'] = "text/plain";
        return help_text

    @cherrypy.expose
    def getwsmevent(self, collection, id):
        uncomp_msg_data = ""
        try:
            msg_doc = mongodb_db[collection].find_one({"_id": bson.objectid.ObjectId(id)})

            msg_data = ""
            if msg_doc is not None:
                msg_data = msg_doc["payload"]

                uncomp_msg_data = zlib.decompress(base64.decodestring(msg_data), -15)
        except Exception, ex:
            return "<Error>%s</Error>" % str(ex)

        return uncomp_msg_data

    @cherrypy.expose
    def getwsmeventdoc(self, collection, id):
        uncomp_msg_data = ""
        try:
            msg_doc = mongodb_db[collection].find_one({"_id": bson.objectid.ObjectId(id)})
            uncomp_msg_data = str(msg_doc)
        except Exception, ex:
            return "<Error>%s</Error>" % str(ex)

        return uncomp_msg_data

    @cherrypy.expose
    def getcollections(self, domain=None, capturedate=None):

        colls = mongodb_db.collection_names()
        new_colls = []
        if domain is not None:
            for col in colls:
                if col.count(domain) > 0:
                    new_colls.append(col)

        if capturedate is not None:
            new_colls_2 = []
            if len(new_colls) > 0:
                for col in new_colls:
                    if col.count(capturedate) > 0:
                        new_colls_2.append(col)

                new_colls = new_colls_2
            else:
                for col in colls:
                    if col.count(capturedate) > 0:
                        new_colls.append(col)

        if capturedate is None and domain is None:
            new_colls = colls

        return str(new_colls)

    @cherrypy.expose
    def getwsmeventdoclist(self, collection, starttime, endtime, device=None, domain=None, service=None, operation=None, status=None, tranid=None, uncompress=None, downloadaszip=None):
        run_start_time = time.time()
        uncomp_msg_data = ""
        try:

            where_clause = {}
            starttime_utc = None
            endtime_utc = None

            if starttime is not None:
                starttime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(starttime, "%Y%m%d%H%M%S"))))
                if endtime is not None:
                    endtime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(endtime, "%Y%m%d%H%M%S"))))
                    where_clause = {"starttimeutc": {"$gt": starttime_utc, "$lt": endtime_utc} }
                else:
                    where_clause["starttimeutc"] = {"$gt": starttime_utc}

            if device is not None:
                where_clause["device"] = device
                pass


            if domain is not None:
                where_clause["domain"] = domain
                pass


            if service is not None:
                where_clause["service"] = service
                pass


            if status is not None:
                where_clause["status"] = status
                pass

            if operation is not None:
                where_clause["operation"] = operation
                pass

            if tranid is not None:
                where_clause["tranid"] = tranid
                pass


            if downloadaszip is not None:
                z_name = "%s.zip" % uuid.uuid4()

                file = zipfile.ZipFile("%s" % z_name , "w", allowZip64=True)
                now = time.localtime(time.time())[:6]
                for msg_doc in mongodb_db[collection].find(where_clause).sort([("starttimeutc", pymongo.ASCENDING)]):
                    info = zipfile.ZipInfo("%s_%s_%s.xml" % (msg_doc["service"], msg_doc["tranid"], msg_doc["payload_type"]))
                    info.date_time = now
                    info.compress_type = zipfile.ZIP_DEFLATED
                    file.writestr(info,zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15))

                file.close()
                file = open("%s" % z_name, "rb")
                uncomp_msg_data = file.read()
                file.close()
                os.remove(z_name)
                cherrypy.response.headers['Content-type'] = "application/zip";

            else:
                uncomp_msg_data = "["
                num_rows = 0
                for msg_doc in mongodb_db[collection].find(where_clause).sort([("starttimeutc", pymongo.ASCENDING)]):
                    num_rows = num_rows + 1
                    if uncompress is not None:
                        msg_doc[u"payload"] = zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15)
                    uncomp_msg_data = uncomp_msg_data + str(msg_doc) + "\n"

                uncomp_msg_data = uncomp_msg_data + "] \n"
                elapsed_time = time.time() - run_start_time
                uncomp_msg_data = uncomp_msg_data + "Fetched %i rows in %i seconds.\n" % (num_rows, elapsed_time)
                cherrypy.response.headers['Content-type'] = "text/plain";

        except Exception, ex:
            return "<Error>%s</Error>" % str(ex)

        return uncomp_msg_data


    @cherrypy.expose
    def getwsmtranevents(self, collection, starttimeutc, tranid, device=None, domain=None, service=None, operation=None, status=None, uncompress=None, downloadaszip=None):
        run_start_time = time.time()
        uncomp_msg_data = ""
        try:

            where_clause = {}
            starttime_utc = None
            endtime_utc = None

            if starttimeutc is not None:
               where_clause["starttimeutc"] = int(starttimeutc)

            if device is not None:
                where_clause["device"] = device
                pass


            if domain is not None:
                where_clause["domain"] = domain
                pass


            if service is not None:
                where_clause["service"] = service
                pass


            if status is not None:
                where_clause["status"] = status
                pass

            if operation is not None:
                where_clause["operation"] = operation
                pass

            if tranid is not None:
                where_clause["tranid"] = tranid
                pass


            if downloadaszip is not None:
                z_name = "%s.zip" % uuid.uuid4()

                file = zipfile.ZipFile("%s" % z_name , "w", allowZip64=True)
                now = time.localtime(time.time())[:6]
                for msg_doc in mongodb_db[collection].find(where_clause).sort([(u"starttimeutc", pymongo.ASCENDING)]):
                    dte = datetime.datetime.fromtimestamp(msg_doc[u"starttimeutc"]).strftime("%Y%m%d%H%M%S")
                    info = zipfile.ZipInfo("%s_%s_%s_%s.xml" % (dte, msg_doc[u"service"], msg_doc[u"tranid"], msg_doc[u"payload_type"]))
                    info.date_time = now
                    info.compress_type = zipfile.ZIP_DEFLATED
                    file.writestr(info,zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15))

                file.close()
                file = open("%s" % z_name, "rb")
                uncomp_msg_data = file.read()
                file.close()
                os.remove(z_name)
                cherrypy.response.headers['Content-type'] = "application/zip";
                cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Payloads_tid-%s.zip" % (tranid)

            else:
                uncomp_msg_data = "["
                num_rows = 0
                for msg_doc in mongodb_db[collection].find(where_clause).sort([(u"starttimeutc", pymongo.ASCENDING)]):
                    num_rows = num_rows + 1
                    if uncompress is not None:
                        msg_doc[u"payload"] = zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15)
                    uncomp_msg_data = uncomp_msg_data + str(msg_doc) + "\n"

                uncomp_msg_data = uncomp_msg_data + "] \n"
                elapsed_time = time.time() - run_start_time
                uncomp_msg_data = uncomp_msg_data + "Fetched %i rows in %i seconds.\n" % (num_rows, elapsed_time)
                cherrypy.response.headers['Content-type'] = "text/plain";

        except Exception, ex:
            return "<Error>%s</Error>" % str(ex)

        return uncomp_msg_data

    @cherrypy.expose
    def getwsmtraneventszipfromtrankeys(self, keystr):
        """
        keys strings are space delimited and in format: collection:request_message_id:response_message_id:be_request_message_id:be_response_message_id

"20160902.TestSplunk:57c9e0084c9ff841320dd2c2::: 20160902.TestSplunk:57c9e0084c9ff841320dd2be:57c9e0084c9ff841320dd2bf:57c9e0084c9ff841320dd2c0:57c9e0084c9ff841320dd2c1 20160902.TestSplunk:57c9dff94c9ff841320dd2ba:57c9dff94c9ff841320dd2bb:57c9dff94c9ff841320dd2bc:57c9dff94c9ff841320dd2bd 20160902.TestSplunk:57c9df804c9ff841320dd2b6:57c9df804c9ff841320dd2b7:57c9df804c9ff841320dd2b8:57c9df814c9ff841320dd2b9 20160902.TestSplunk:57c9df084c9ff841320dd2b2:57c9df084c9ff841320dd2b3:57c9df084c9ff841320dd2b4:57c9df084c9ff841320dd2b5"

created with search like:
index=esb*_syslog wsm_evt | getdpwsm | fields * | fillnull value="" collection,request_message_id,response_message_id,be_request_message_id,be_response_message_id| eval tran_key=collection.":".request_message_id.":".response_message_id.":".be_request_message_id.":".be_response_message_id    | stats list(tran_key) as tk | nomv tk

        """
        run_start_time = time.time()

        try:
            #print keystr
            decode_tks = base64.urlsafe_b64decode(keystr)
            #print "Decoded:", len(decode_tks), decode_tks
            decomped_tks = gzip.zlib.decompress(decode_tks)
            #print decomped_tks
            #tran_key_list = keystr.split(" ")
            tran_key_list = decomped_tks.split(" ")

            col_dict = {}
            for tk in tran_key_list:
                (tk_col, tk_req_id, tk_res_id, tk_be_req_id, tk_be_res_id) = tk.split(":")

                if tk_col != "":
                    if not col_dict.has_key(tk_col):
                        col_dict[tk_col] = []

                    if tk_req_id != "":
                        col_dict[tk_col].append(bson.objectid.ObjectId(tk_req_id))

                    if tk_res_id != "":
                        col_dict[tk_col].append(bson.objectid.ObjectId(tk_res_id))

                    if tk_be_req_id != "":
                        col_dict[tk_col].append(bson.objectid.ObjectId(tk_be_req_id))

                    if tk_be_res_id != "":
                        col_dict[tk_col].append(bson.objectid.ObjectId(tk_be_res_id))

            if len(col_dict) == 0:
                return "No collections and keys found."

            z_name = "%s.zip" % uuid.uuid4()

            file = zipfile.ZipFile("%s" % z_name , "w", allowZip64=True)
            now = time.localtime(time.time())[:6]

            f_count = 0
            for collection, ids in col_dict.items():
                where_clause = {"_id": {"$in": ids} }
#                print str(where_clause)
                for msg_doc in mongodb_db[collection].find(where_clause):
                    #print "here"
                    f_count = f_count + 1
                    dte = datetime.datetime.fromtimestamp(msg_doc[u"starttimeutc"]).strftime("%Y%m%d%H%M%S")
                    info = zipfile.ZipInfo("%s_%s_%s_%s.xml" % (dte, msg_doc[u"service"], msg_doc[u"tranid"], msg_doc[u"payload_type"]))
                    info.date_time = now
                    info.compress_type = zipfile.ZIP_DEFLATED
                    file.writestr(info,zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15))

            file.close()
            file = open("%s" % z_name, "rb")
            uncomp_msg_data = file.read()
            file.close()
            os.remove(z_name)

            if f_count == 0:
                cherrypy.response.headers['Content-type'] = "text/plain";
                return "No rows returned."

            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Payloads_%s_%i.zip" % (datetime.datetime.now().strftime("%Y%m%d_%H%M"), f_count)
            cherrypy.response.headers['Content-type'] = "application/zip";

            return uncomp_msg_data


        except Exception, ex:
            cherrypy.response.headers['Content-type'] = "text/plain";
            return "Error: %s" % str(ex)

        return uncomp_msg_data


    @cherrypy.expose
    def downloadwsmevents(self, collection, starttime=None, endtime=None, device=None, service=None, payload=None):
        """

Download wsm events.
        """
        run_start_time = time.time()

        try:

            where_clause = {}

            if starttime is not None:
                starttime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(starttime, "%Y%m%d%H%M%S"))))
                if endtime is not None:
                    endtime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(endtime, "%Y%m%d%H%M%S"))))
                    where_clause = {"starttimeutc": {"$gt": starttime_utc, "$lt": endtime_utc} }
                else:
                    where_clause["starttimeutc"] = {"$gt": starttime_utc}

            if device is not None:
                where_clause["device"] = device
                pass

            if service is not None:
                where_clause["service"] = service
                pass

            z_name = "%s.zip" % uuid.uuid4()

            file = zipfile.ZipFile("%s" % z_name , "w", allowZip64=True)
            now = time.localtime(time.time())[:6]

            f_count = 0
            for msg_doc in mongodb_db[collection].find(where_clause):
                #print "here"

                dte = datetime.datetime.fromtimestamp(msg_doc[u"starttimeutc"]).strftime("%Y%m%d%H%M%S")
                info = zipfile.ZipInfo("%s_%s_%s_%s.xml" % (dte, msg_doc[u"service"], msg_doc[u"tranid"], msg_doc[u"payload_type"]))
                info.date_time = now
                info.compress_type = zipfile.ZIP_DEFLATED
                msg_data = zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15)
                if payload is not None:
                    if not msg_data.count(payload) > 0:
                        continue

                file.writestr(info, msg_data)
                f_count = f_count + 1

            file.close()
            file = open("%s" % z_name, "rb")
            uncomp_msg_data = file.read()
            file.close()
            os.remove(z_name)

            if f_count == 0:
                cherrypy.response.headers['Content-type'] = "text/plain";
                return "No rows returned."

            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Payloads_%s_%s_%i.zip" % (collection, datetime.datetime.now().strftime("%Y%m%d_%H%M"), f_count)
            cherrypy.response.headers['Content-type'] = "application/zip";

            return uncomp_msg_data


        except Exception, ex:
            cherrypy.response.headers['Content-type'] = "text/plain";
            return "Error: %s" % str(ex)

        return uncomp_msg_data


    @cherrypy.expose
    def downloadwsmeventsbypayload(self, date, environment, payload, starttime=None, endtime=None, device=None, domain=None, service=None):
        """

Download wsm events by payload.
        """
        run_start_time = time.time()

        try:

            new_colls = []
            colls = mongodb_db.collection_names()
            for col in colls:
                if col.count(date) > 0:
                    if domain is not None:
                        if col.count(domain):
                            new_colls.append(col)
                    else:
                        new_colls.append(col)

            where_clause = {}

            if starttime is not None:
                starttime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(starttime, "%Y%m%d%H%M%S"))))
                if endtime is not None:
                    endtime_utc = calendar.timegm(time.gmtime(time.mktime(time.strptime(endtime, "%Y%m%d%H%M%S"))))
                    where_clause = {"starttimeutc": {"$gt": starttime_utc, "$lt": endtime_utc} }
                else:
                    where_clause["starttimeutc"] = {"$gt": starttime_utc}

            if device is not None:
                if environment == "dev1":
                    if device not in dev_devices:
                        cherrypy.response.headers['Content-type'] = "text/plain";
                        return "Invalid Device specified?"
                    else:
                        where_clause["device"] = device

                else:
                    if environment == "sit1":
                        if device in sit1_devices:
                            cherrypy.response.headers['Content-type'] = "text/plain";
                            return "Invalid Device specified?"
                        else:
                            where_clause["device"] = device
                    else:
                        if environment == "sit2":
                            if device in sit2_devices:
                                cherrypy.response.headers['Content-type'] = "text/plain";
                                return "Invalid Device specified?"
                            else:
                                where_clause["device"] = device
                        else:
                            if environment == "prod":
                                if device in prod_devices:
                                    cherrypy.response.headers['Content-type'] = "text/plain";
                                    return "Invalid Device specified?"
                                else:
                                    where_clause["device"] = device
            else:
                if environment == "dev1":
                    where_clause["device"] = {"$in": dev_devices}
                else:
                    if environment == "sit1":
                        where_clause["device"] = {"$in": sit1_devices}
                    else:
                        if environment == "sit2":
                            where_clause["device"] = {"$in": sit2_devices}
                        else:
                            if environment == "prod":
                                where_clause["device"] = {"$in": prod_devices}

            if service is not None:
                where_clause["service"] = service
                pass

            z_name = "%s.zip" % uuid.uuid4()

            file = zipfile.ZipFile("%s" % z_name , "w", allowZip64=True)
            now = time.localtime(time.time())[:6]

            f_count = 0
            for col in new_colls:
                for msg_doc in mongodb_db[col].find(where_clause):
                    #print "here"

                    dte = datetime.datetime.fromtimestamp(msg_doc[u"starttimeutc"]).strftime("%Y%m%d%H%M%S")
                    info = zipfile.ZipInfo("%s_%s_%s_%s.xml" % (dte, msg_doc[u"service"], msg_doc[u"tranid"], msg_doc[u"payload_type"]))
                    info.date_time = now
                    info.compress_type = zipfile.ZIP_DEFLATED
                    msg_data = zlib.decompress(base64.decodestring(msg_doc[u"payload"]), -15)
                    if payload is not None:
                        if not msg_data.count(payload) > 0:
                            continue

                    file.writestr(info, msg_data)
                    f_count = f_count + 1

            file.close()
            file = open("%s" % z_name, "rb")
            uncomp_msg_data = file.read()
            file.close()
            os.remove(z_name)

            if f_count == 0:
                cherrypy.response.headers['Content-type'] = "text/plain";
                return "No rows returned."

            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Payloads_%s_%i.zip" % (datetime.datetime.now().strftime("%Y%m%d_%H%M"), f_count)
            cherrypy.response.headers['Content-type'] = "application/zip";

            return uncomp_msg_data


        except Exception, ex:
            cherrypy.response.headers['Content-type'] = "text/plain";
            return "Error: %s" % str(ex)

        return uncomp_msg_data



conf = {
     '/': {
             'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/xml')],
         }
}

cherrypy.config.update({'server.socket_host': '0.0.0.0',
                    'server.socket_port': 25015,
                    })

print "Before Here"

#cherrypy.quickstart(WSMPushRestService("esbdpd01", "AccountManagement", cdb_db), '/', conf)
cherrypy.tree.mount(WSMPayloadServer(), '/', conf)
cherrypy.engine.signal_handler.subscribe()
cherrypy.engine.start()
#cherrypy.engine.

print "Here"
cherrypy.engine.block()
print "Not Here"


