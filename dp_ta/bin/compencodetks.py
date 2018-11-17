#!/opt/splunk/bin/python 

import sys
import csv
import splunk.Intersplunk
import os
import gzip
import base64

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
#
#     else:
#         if arg.count("=") > 1 or arg.count("=") <= 0:
#             splunk.Intersplunk.parseError("Invalid argument. Valid options are includeblob/dontfixpdgheader/extractblob/excludepayload/convertblob=<true|false> bloblimit/extractbloblimit=<integer>")

    i = i + 1


results = splunk.Intersplunk.readResults(None, None, True)
#sys.stderr.write("Results!" + str(results[0].keys()) + "\n")
messages = {}

if len(results) > 0:
    try:
        if results[0].has_key("tk"):
            tran_keys = results[0]["tk"]
            comped_tran_keys = gzip.zlib.compress(tran_keys,9)
            b64_comped_tran_keys = base64.urlsafe_b64encode(comped_tran_keys)
            results[0]["tk"] = b64_comped_tran_keys
            #sys.stderr.write("tk:" + str(b64_comped_tran_keys) + "\n")
    except Exception, ex:
        splunk.Intersplunk.addErrorMessage(messages, "Exception occurred.  " + str(ex))

splunk.Intersplunk.outputResults(results, messages=messages)
