<?xml version="1.0" encoding="UTF-8"?>
<!--
 * Name:           splunk_wsm.xsl
 * Description:    Implementation of transaction accounting message formats
                   specific for easy splunk indexing.
 * Author:         Martin Legend Pieterse/ Hannes Wagener 

 * Disclaimer:     You are free to use this code in any way you like, subject to the
                   Python & IBM disclaimers & copyrights. I make no representations
                   about the suitability of this software for any purpose. It is
                   provided "AS-IS" without warranty of any kind, either express or
                   implied.
-->

<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:func="http://exslt.org/functions"
                xmlns:fn="http://www.w3.org/2005/xpath-functions"
                xmlns:date="http://exslt.org/dates-and-times"
                xmlns:dp="http://www.datapower.com/schemas/management"
                xmlns:dpe="http://www.datapower.com/extensions"
                xmlns:dpc="http://www.datapower.com/schemas/management"
                xmlns:dple="http://www.datapower.com/extensions/local"
                xmlns:dpt="http://www.datapower.com/schemas/transactions"
                xmlns:env="http://www.w3.org/2003/05/soap-envelope"
                xmlns:env11="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                xmlns:wse="http://schemas.xmlsoap.org/ws/2004/08/eventing"
                xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration"
                xmlns:wsman="http://schemas.xmlsoap.org/ws/2005/02/management"
                xmlns:wsmancat="http://schemas.xmlsoap.org/ws/2005/02/wsmancat"
                exclude-result-prefixes="func date dpc dpe dple dpt wsa wse wsen wsman wsmancat"
                extension-element-prefixes="dpc dpe date">

    <xsl:include href="store:///dp/wsm-library.xsl" dpe:ignore-multiple="yes"/>
    <xsl:include href="store:///dp/msgcat/mplane.xml.xsl" dp:ignore-multiple="yes"/>
    <xsl:variable name="Debug" select="dpe:variable('var://system/ws-mgmt/debug')"/>

    <!--
       Available Context variables are:
         var://context/wsm/verbosity: 'Content' element from Pull Request
         var://context/wsm/events: transaction accounting message
    -->

    <xsl:template match="/">
        <xsl:variable name="verbosity2" select="dpe:variable('var://context/wsm/verbosity')"/>
        <xsl:variable name="verbosity">
            <xsl:choose>
                <xsl:when test="$verbosity2=''">
                    <xsl:value-of select="'full'"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$verbosity2"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="events" select="dpe:variable('var://context/wsm/events')"/>
        <dpe:set-variable name="'var://context/req/fault'" value="string('1')"/>

        <xsl:for-each select="$events//dpt:transaction">
            <transaction>
                <xsl:for-each select="*">
                    <xsl:choose>
                        <!-- Fields requiring apostrophes -->
                        <xsl:when test="name() = 'ws-operation'
                            or name() = 'request-url'
                            or name() = 'final-url'
                            or name() = 'backend-url'
                            or name() = 'fault-code'
                            or name() = 'ws-client-id'
                            or name() = 'service-port'
                            or name() = 'webservice'">
                            <xsl:call-template name="withQuot"/>
                        </xsl:when>
                        <xsl:when test="name() = 'start-time'">
                            <xsl:call-template name="startTime"/>
                        </xsl:when>
                        <!-- Payload handling -->
                        <xsl:when test="name() = 'request-message'
                            or name() = 'response-message'">
                            <xsl:call-template name="compressAndEncode"/>
                        </xsl:when>
                        <!-- Backend message handling -->
                        <xsl:when test="name() = 'backend-message'">
                            <xsl:for-each select="*">
                                <xsl:choose>
                                    <xsl:when test="name() = 'request-message'
                                        or name() = 'response-message'">
                                        <xsl:call-template name="be_compressAndEncode"/>
                                    </xsl:when>
                                    <xsl:when test="name() = 'backend-url'">
                                        <xsl:call-template name="be_withQuot"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:call-template name="be_withoutApos"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:when test="name() = 'fault-message'">
                            <xsl:call-template name="withQuot"/>
                            <xsl:text>status=fail </xsl:text>
                            <dpe:set-variable name="'var://context/req/fault'" value="string('2')"/>
                        </xsl:when>
                        <!-- Any other fields -->
                        <xsl:otherwise>
                            <xsl:call-template name="withoutApos"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
                <xsl:if test="dpe:variable('var://context/req/fault') = '1'">
                    <xsl:text>status=ok </xsl:text>
                </xsl:if>
            </transaction>
        </xsl:for-each>
    </xsl:template>
    <!-- Custom Templates -->
    <xsl:template name="withQuot">
        <xsl:value-of select="translate(name(), '-','_')"/>
        <xsl:text>=&quot;</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>&quot; </xsl:text>
    </xsl:template>
    <xsl:template name="withoutApos">
        <xsl:value-of select="translate(name(), '-','_')"/>
        <xsl:text>=</xsl:text>
        <xsl:value-of select="concat(., string(' '))"/>
    </xsl:template>
    <xsl:template name="compressAndEncode">
        <xsl:value-of select="translate(name(), '-','_')"/>
        <xsl:text>=&quot;</xsl:text>

        <xsl:variable name="payloadstr">
        	<dpe:serialize select="child::node()" omit-xml-decl="yes" />
        </xsl:variable>
        <xsl:value-of select="dpe:deflate($payloadstr)"/>
        <xsl:text>&quot; </xsl:text>
    </xsl:template>
    <xsl:template name="startTime">
        <xsl:value-of select="translate(name(), '-','_')"/>
        <xsl:text>=&quot;</xsl:text>
        <xsl:value-of select="translate(., '&#10;', '')"/>
        <xsl:text>&quot; </xsl:text>
        <!--start_time_utc-->
        <xsl:text>start_time_utc=&quot;</xsl:text>
        <xsl:value-of select="./@utc"/>
        <xsl:text>&quot; </xsl:text>
    </xsl:template>
    <!-- Backend -->
    <xsl:template name="be_withQuot">
        <xsl:value-of select="concat('be_', translate(name(), '-','_'))"/>
        <xsl:text>=&quot;</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>&quot; </xsl:text>
    </xsl:template>
    <xsl:template name="be_withoutApos">
        <xsl:value-of select="concat('be_', translate(name(), '-','_'))"/>
        <xsl:text>=</xsl:text>
        <xsl:value-of select="concat(., string(' '))"/>
    </xsl:template>

    <xsl:template name="be_compressAndEncode">
        <xsl:value-of select="concat('be_', translate(name(), '-','_'))"/>
        <xsl:text>=&quot;</xsl:text>

        <xsl:variable name="payloadstr">
        	<dpe:serialize select="child::node()" omit-xml-decl="yes" />
        </xsl:variable>
        <xsl:value-of select="dpe:deflate($payloadstr)"/>

        <xsl:text>&quot; </xsl:text>
    </xsl:template>

    <!--
    <xsl:template name="be_compressAndEncode">
        <xsl:value-of select="concat('be_', translate(name(), '-','_'))"/>
        <xsl:text>=&quot;</xsl:text>
        <xsl:copy-of select="dpe:deflate(.)"/>
        <xsl:text>&quot; </xsl:text>
    </xsl:template>
    -->
</xsl:stylesheet>