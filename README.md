# splunk-ibm-websphere-datapower-add-on
Spunk add-on for IBM Websphere Datapower

By jjjw420 - 2016

## Overview

This is a Splunk modular input for IBM Websphere Datapower Gateways.  
Three types oof input is currently supported"
- IBM Datapower Gateway Statistics

Fetches all relevant statistics required for the device.  Different statistic types can have different fetch frequencies.

- IBM Datapower Gateway WSM Input
An input to subscribe and pull WSM (Web Service Monitoring) records from Datapower.  Currently only the WSM pull subscription is implemented.  Message payloads can be written into splunk, Mongo or as individual files on disk.

- IBM Datapower Configuration Input
Indexes the IBM Datapower Gateway configuration.  Is indexed as json and xml. This allows you search your Datapower configuration and understand dependendencies between objects.   Invaluable if you have hundreds of services running.
The "dpconfig" search command can be used to display the search results or to follow object dependencies and show the relationship between Datapower objects. 


## Features



## Dependencies

## Setup

## Logging

## Troubleshooting

## Conversion to the IBM Datapower REST interface and Python3 support.  
Currently the XML Management (SOMA) interface is used to query the information from Datapower as that was the only option at the time of writing this add on.   A REST intereface is now available on Datapower and if used can make the add-on more light weight and will allow the Spluk event to be logged as a JSON response or in the current key-value pair output using the XML interface.  

Conversion to the REST interface has started.

Splunk will be using Python 3 from early 2020.  Conversion to support Python3 has started.

## DISCLAIMER
You are free to use this code in any way you like, subject to the Python & IBM disclaimers & copyrights. I make no representations about the suitability of this software for any purpose. It is provided "AS-IS" without warranty of any kind, either express or implied. 

