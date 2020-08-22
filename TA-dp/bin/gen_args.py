import json
import lxml.etree

x = """<endpoint>
            <args>
            <arg name="name">
                <title>Device Name</title>
                <description>Name of the Datapower device to monitor.</description>
            </arg>
            <arg name="device_host">
                <title>Datapower Device Hostname or IP</title>
                <description>IP or hostname of the Datapower device to be monitored.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="soma_port">
                <title>SOMA Port</title>
                <description>The XML Management interface(SOMA) port number.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="soma_user">
                <title>The SOMA user</title>
                <description>The user to use when using the XML Management Interface.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
             <arg name="soma_user_password">
                <title>The SOMA user's password</title>
                <description>The users password</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="enable_wsm">
                <title>Enable the WS-M agents on the device.</title>
                <description>Enable the WS-M agents on the device.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_domains">
                <title>Use WS-M to capture transaction statistics.</title>
                <description>Use WS-M to capture transaction statistics. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="use_wsm_transaction_time">
                <title>Use WS-M transaction time as event time</title>
                <description>Use WS-M transaction time as event time.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="wsm_max_rec_size">
                <title>WS-M maximum record size.</title>
                <description>WS-M maximum record size. Defaults to 3000.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


            <arg name="wsm_max_mem">
                <title>WS-M maximum memory.</title>
                <description>WS-M maximum memory. Defaults to 64mb.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_capture_mode">
                <title>WS-M capture mode.</title>
                <description>WS-M capture mode.All, faults or none. Defaults to All.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_buf_mode">
                <title>WS-M buffering mode.</title>
                <description>WS-M buffering mode.  Discard or Buffer. Defaults to Buffer. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_med_enf_metrics">
                <title>WS-M mediation enforcement metrics.</title>
                <description>Capture WS-M mediation enforcement metrics. Defaults to false.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>



            <arg name="wsm_pull">
                <title>WS-M pull subscription.</title>
                <description>WS-M pull subscription.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_interval">
                <title>WS-M pull interval.</title>
                <description>WS-M pull interval. Defaults to 60.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_max_soap_env_size">
                <title>WS-M pull maximum SOAP Envelop size.</title>
                <description>WS-M pull maximum SOAP Envelop size.  Defaults to 511.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_max_elements">
                <title>WS-M pull maximum number of elements.</title>
                <description>The maximum number of elements to return on a pull request.  Defaults to 100.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_pull_use_custom_formatter">
                <title>se the custom Splunk WSM formatter to format the WSM data on the device.</title>
                <description>se the custom Splunk WSM formatter to format the WSM data on the device.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push">
                <title>WS-M push subscription.</title>
                <description>WS-M push subscription.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_host">
                <title>WS-M push server host.</title>
                <description>The host to use for the server to which the WS-M data will be pushed to. </description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_port">
                <title>WS-M push server port.</title>
                <description>The port to use for the server to which the WS-M data will be pushed to. Defaults to 14014.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_server_thread_per_domain">
                <title>WS-M Push server thread per domain.</title>
                <description>Start a WS-M Push server thread per domain.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_push_max_elements">
                <title>WS-M push maximum number of elements.</title>
                <description>The maximum number of elements to send on the push request.  Defaults to 100.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_to_splunk">
                <title>Write WS-M message payloads to Splunk</title>
                <description>Write WS-M message payloads to Splunk.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_to_disk">
                <title>Write WS-M message payloads to disk instead of indexing in Splunk</title>
                <description>Write WS-M message payloads to disk instead of indexing in Splunk.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_folder">
                <title>Folder to write message payloads to.</title>
                <description>Write WS-M message payloads to disk instead of indexing in Splunk.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_use_mongodb">
                <title>Write payloads to a Mongo database.</title>
                <description>Write payloads to a Mongo database instead of writing individual files.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_db_name">
                <title>The mongodb database name.</title>
                <description>The mongodb database to use.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_host">
                <title>The mongodb server host name.</title>
                <description>The mongodb server host name.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_port">
                <title>The mongodb server port.</title>
                <description>The mongodb server port.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_use_auth">
                <title>Use mongodb authorisation.</title>
                <description>Use mongodb authorisation.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_user">
                <title>The mongodb database user.</title>
                <description>The mongodb database to insert the payloads into.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>

            <arg name="wsm_msg_payloads_mongodb_password">
                <title>The mongodb user password.</title>
                <description>The mongodb user password.</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            
            <arg name="wsm_msg_payloads_mongodb_retention">
                <title>Enable auto retention</title>
                <description>Enable auto retention</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            
            <arg name="wsm_msg_payloads_mongodb_retention_period">
                <title>Auto retention period</title>
                <description>Auto retention period</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>


        </args>
    </endpoint>
"""    

c_t = """        
    {name}_argument = splunklib.modularinput.Argument("{name}")
    {name}_argument.data_type = splunklib.modularinput.Argument.data_type_number
    {name}_argument.title = "{title}"
    {name}_argument.description = "{description}"
    {name}_argument.required_on_create = {required_on_create}
    {name}_argument.required_on_edit = {required_on_edit}
    scheme.add_argument({name}_argument)"""

doc = lxml.etree.fromstring(x)

nl = doc.xpath("//arg")

if len(nl) > 0:
    for n in nl:
        name = ""
        title = ""
        description = ""
        required_on_create = ""
        required_on_edit = ""
        name = n.attrib["name"]

        #
        # print(name)

        for c in n:
            if c.tag == "title":
                title = c.text
            elif c.tag == "description":
                description =  c.text
            elif c.tag == "required_on_create":
                required_on_create =  c.text.capitalize()
            elif c.tag == "required_on_edit":
                required_on_edit =  c.text.capitalize()
        print(c_t.format(name=name, title=title, description=description, required_on_create=required_on_create, required_on_edit=required_on_edit))            

