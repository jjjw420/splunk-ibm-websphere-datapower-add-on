import requests
import lxml.etree
import uuid

soma_user = "admin"
soma_user_password = "datapower"
device_host = "localdp"
soma_port = "5550"

soma_session = requests.Session()
soma_session.auth = (soma_user, soma_user_password)
soma_session.verify = False


soma_url = "https://{device_host}:{soma_port}/service/mgmt/3.0"

def get_domains(soma_session, device_host, soma_port, soma_user, soma_user_password):
    domain_status = {"domain": "default", "status_class": "DomainStatus"}
    domain_status_req = get_status_req.format(**domain_status)

    print "Getting domains from " + device_host

    domain_list = None
    try:
        #r = requests.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_status_req, auth=(soma_user, soma_user_password), verify=False)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=domain_status_req)

        if r.status_code != 200:
            print "Get of domains for %s failed.  Status code: %i." % (device_host, r.status_code)
            return None
        else:
            print "Get of domains for %s OK!.  Status code: %i." % (device_host, r.status_code)

        doc = lxml.etree.fromstring(r.content)

        d_nl = doc.xpath("//Domain")

        if len(d_nl) > 0:
            domain_list = []
            for d in d_nl:
                domain_list.append(d.text)

    except Exception, ex:
        print "Exception occurred while getting domains. Exception: " + str(ex)

    return domain_list



get_status_req = """<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
    <env:Body>
        <dp:request domain="{domain}" xmlns:dp="http://www.datapower.com/schemas/management">
            <dp:get-status class="{status_class}"/>
        </dp:request>
    </env:Body>
</env:Envelope>
"""


wsm_unsub_pull = """<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management">
   <env:Header>
      <wsa:To>/wsman?ResourceURI=(wsman:datapower.com/resources/2005/07/ws-gateway)</wsa:To>
      <wsa:ReferenceProperties>
         <dpt:Domain xmlns:dpt="http://www.datapower.com/schemas/transactions">{domain}</dpt:Domain>
         <wse:Identifier>uuid:{enumeration_context}</wse:Identifier>
      </wsa:ReferenceProperties>
      <wsa:ReplyTo>
         <wsa:Address env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
      </wsa:ReplyTo>
      <wsa:Action env:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/08/eventing/Unsubscribe</wsa:Action>
      <wsman:MaxEnvelopeSize env:mustUnderstand="true">51200</wsman:MaxEnvelopeSize>
      <wsman:OperationTimeout>PT60.000S</wsman:OperationTimeout>
      <wsman:System>wsman:datapower.com/resources/2005/07/ws-management</wsman:System>
      <wsa:MessageID>{msg_id}</wsa:MessageID>
   </env:Header>
   <env:Body>
      <wse:Unsubscribe>
         <wsen:EnumerationContext>uuid:{enumeration_context}</wsen:EnumerationContext>
      </wse:Unsubscribe>
   </env:Body>
</env:Envelope>
"""

domain_list = get_domains(soma_session, device_host, soma_port, soma_user, soma_user_password)

if domain_list is not None:
    for domain in domain_list:
        print "Doing domain: %s" % domain
        wsm_agent_spoolers_status_o = {"domain": "default", "status_class": "WSMAgentSpoolers"}
        wsm_agent_spoolers_req = get_status_req.format(**wsm_agent_spoolers_status_o)
        r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=wsm_agent_spoolers_req)

        if r.status_code == 200:
            print "WSM Agent spoolers ok.", r.content
            doc = lxml.etree.fromstring(r.content)
            nl = doc.xpath("//Context")
            if nl is not None:
                for n in nl:
                    wsm_unsub_pull_req = wsm_unsub_pull.format(domain=domain, enumeration_context=n.text, msg_id=uuid.uuid4())
                    print wsm_unsub_pull_req
                    u_r = soma_session.post(soma_url.format(device_host=device_host, soma_port=soma_port), data=wsm_unsub_pull_req)
                    if u_r.status_code != 200:
                        print "Unsubscribe failed."
                    else:
                        print "Unsubscribed!", u_r.content
            else:
                print "No context?"

        else:
            print "Failed to get agent spoolers for domain %s" % domain
