# splunk-ibm-websphere-datapower-add-on - dp_ta

By Hannes Wagener - 2016

## Overview

This is a Splunk modular input add-on for IBM Websphere Datapower.
It fetches data via the XML management interface and WS-M.

Created from the Splunk modular input examples.

## Features

* Simple UI based configuration via Splunk Manager
*

## Dependencies

* Splunk 6.0+
* CodernityDB if payloads are not to be indexed in splunk.

## Setup

* Restart Splunk

use admin
db.createUser({user:"admin", pwd:"mongodb!", roles:[{role:"root", db:"admin"}]})


db.createUser({user:"splunk", pwd:"splunk", roles:[{role:"readWrite", db:"dptrans"}]})


var user = {
  "user" : "splunk",
  "pwd" : "splunk",
  roles : [
      {
          "role" : "dbOwner",
          "db" : "dptrans"
      }
  ]
}

db.createUser(user);


## Logging

Any modular input log errors will get written to $SPLUNK_HOME/var/log/splunk/splunkd.log.  Debug logging can be "enabled by changing the "ExecProcessor" property under "Server logging" to DEBUG.

## Troubleshooting

* You are using Splunk 6+


## DISCLAIMER
You are free to use this code in any way you like, subject to the Python & IBM disclaimers & copyrights. I make no representations about the suitability of this software for any purpose. It is provided "AS-IS" without warranty of any kind, either express or implied.
