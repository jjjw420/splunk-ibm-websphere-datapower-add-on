[dpinput://<name>]

*Datapower Device Name
device_name= <value>

*IP or hostname of the device
device_host= <value>

*The SOMA port on the device.  Defaults to 5550
soma_port= <value>

*The user to use when querying the device.
soma_user= <value>

*The password for the user.
soma_user_password= <value>

*How often to run the Datapower Input script
dpinput_interval= <value>

*enable statistics
enable_stats= <value>

*enable statistics in domains
enable_stats_domains= <value>

*cpu usage interval
cpu_usage_int = <value>

*connections accepted interval
conns_accepted_int = <value>

*memory status interval
memory_int = <value>

*Only log stats for interfaces with IP Addresses.
only_eth_ints_with_ips= <value>

*tx/rx kbps throughput interval
tx_rx_kbps_thruput_int = <value>

*network status interval
network_int = <value>

*system usage interval
system_usage_int = <value>


*capture Object Status
object_status= <value>

*capture Object Status int
object_status_int= <value>

*capture HTTP related statistics
http_status= <value>

*capture HTTP int
http_int= <value>

*Capture Service related memory statistics
service_memory_status= <value>

*Capture SQL related statistics and status
sql_status= <value>
sql_int= <value>

*Capture MQ related statistics and status
mq_status= <value>
mq_int=<value>

*Capture Hardware and sensor related stats
sensors_status= <value>
*environmental sensors interval
sensors_int = <value>


*Capture Stylesheet and XML related statistics and statuses
xslt_status= <value>
xslt_int=<value>

*Capture WS operation statistics
ws_op_status= <value>
ws_op_status_int=<value>

*Capture WebAppFw accepted and rejected stats.
web_app_fw_stats= <value>
web_app_fw_int= <value>


*Use WS-M to capture transactions
use_wsm= <value>
wsm_stats_int= <value>

*Enable the WS-M agents.
enable_wsm= <value>

*Use WS-M in the following domains.  comma separated.
wsm_domains= <value>

*Use WS-M transaction time as event time
use_wsm_transaction_time = <value>

*WS-M maximum record size.
wsm_max_rec_size= <value>

*WS-M maximum memory usage.
wsm_max_mem= <value>

*WS-M capture mode.
wsm_capture_mode= <value>

*WS-M buffering mode.
wsm_buf_mode= <value>

*WS-M mediation enforcement metrics.
wsm_med_enf_metrics= <value>

*WS-M pull subscription
wsm_pull= <value>

*WS-M Pull interval
wsm_pull_interval= <value>

*WS-M Pull maximum SOAP Envelope size
wsm_pull_max_soap_env_size= <value>

*WS-M Pull maximum number of elements
wsm_pull_max_elements= <value>

*Use the custom splunk_dpinput wsm formatter
wsm_pull_use_custom_formatter= <value>




*WS-M Push subscription
wsm_push= <value>


*WS-M push host
wsm_push_server_host= <value>

*WS-M push port
wsm_push_server_port= <value>

*WS-M server thread per domain
wsm_push_server_thread_per_domain= <value>


*WS-M push subscription
wsm_push_max_elements= <value>

*Write WS-M payloads to disk or index in splunk
wsm_msg_payloads_to_disk= <value>

*Write WS-M payloads to disk or index in splunk
wsm_msg_payloads_folder= <value>

*Write WS-M message payloads to a Mongo database in order to save on file-system inodes
wsm_msg_payloads_use_mongodb= <value>

*MongoDB database name
wsm_msg_payloads_mongodb_db_name= <value>

*MongoDB database host
wsm_msg_payloads_mongodb_host= <value>

*MongoDB database port
wsm_msg_payloads_mongodb_port= <value>


*MongoDB database use auth
wsm_msg_payloads_mongodb_use_auth= <value>

*MongoDB database user
wsm_msg_payloads_mongodb_user= <value>

*MongoDB database password
wsm_msg_payloads_mongodb_password= <value>



