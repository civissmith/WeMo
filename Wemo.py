#!/usr/bin/python -B
################################################################################
# Copyright (c) 2013 Phil Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
################################################################################
# @Title: Wemo.py
#
# @Author: Phil Smith
#
# @Date: 17-Aug-2013 2:20 AM
#
# @Project: Wemo
#
# @Purpose: This module serves as the object model for Wemo devices.
#
################################################################################
import re
import time
import fcntl
import struct
import socket

#
# WemoBase class represents generic Wemo devices.
#{
class WemoBase(object):
  """
  Represents the basic Wemo functionality.
  """
  #
  # WemoBase::__init__() - Initialize basic data for Wemo
  #{
  def __init__(self, location, uuid='None', dev_type='None'):


    # Strip off the trailing slash since the commands need to have a leading slash.
    if location[-1] == '/':
       self.location = location[:-1]
    else:
       self.location = location

    self.uuid  = uuid
    self.dev_type = dev_type
    # Strip out the URL information to get the IP address and port.
    self.ip, self.port = location.strip('http://').strip('/setup.xml').split(':')
    self.port = int(self.port)
    self.TIMEOUT = 2.5 # Seconds
    self.LOCAL_GW_ADDR = '192.168.0.1'
    self.LOCAL_GW_PORT = 80
    self.name = self.get_friendly_name()
    self.current_state = self.get_current_state()

  #}
  # End of WemoBase::__init__() 
  #
    
  #
  # WemoBase::__str__() - String representation
  #{
  def __str__(self):
    dev_str = "%s - %s:%s" % ( self.name, self.ip, self.port )
    return dev_str
  #}
  # End of WemoBase::__str__() 
  #

  #
  # WemoBase::send_to_wemo() - Sends a SOAP+payload message to the Wemo hardware.
  #                            Returns the response from the hardware.
  #{
  def send_to_wemo(self, message):
    #
    # Setup a socket connection to the device.
    #
    socket.setdefaulttimeout(self.TIMEOUT)
    cmd_addr = get_active_iface_addr((self.LOCAL_GW_ADDR, self.LOCAL_GW_PORT))

    # Wemo commands are sent over TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    # Allow the kernel to reuse the addr without TIME_WAIT expiring
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.connect((self.ip, self.port ))
    sock.sendto( message, (self.ip, self.port ) )
    response = sock.recv(1024)
    sock.close()
    return response
  #}
  # End of WemoBase::send_to_wemo()
  #

  #
  # WemoBase::get_soap_payload() - Returns a SOAP header and payload to send
  #                                to a WeMo device.
  #{
  def get_soap_payload(self, service, action):
    SOAP = ''
    payload = ''
    host = ''
    host = "Host: %s:%s\r\n" % (self.ip, self.port)
    ####################
    # Services         #
    ####################

    if service.upper() == 'SET_BIN_STATE':
      SOAP = 'POST /upnp/control/basicevent1 HTTP/1.1\r\n' +\
             'SOAPAction: "urn:Belkin:service:basicevent:1#SetBinaryState"\r\n' +\
             host +\
             'Content-Type: text/xml\r\n' +\
             'Content-Length: 333\r\n\r\n'

    if service.upper() == 'GET_BIN_STATE':
      SOAP = 'POST /upnp/control/basicevent1 HTTP/1.1\r\n' +\
             'SOAPAction: "urn:Belkin:service:basicevent:1#GetBinaryState"\r\n' +\
             host +\
             'Content-Type: text/xml\r\n' +\
             'Content-Length: 305\r\n\r\n'

    if service.upper() == 'GET_FRIEND_NAME':
      SOAP = 'POST /upnp/control/basicevent1 HTTP/1.1\r\n' +\
             'SOAPAction: "urn:Belkin:service:basicevent:1#GetFriendlyName"\r\n' +\
             host +\
             'Content-Type: text/xml\r\n' +\
             'Content-Length: 336\r\n\r\n'

    ####################
    # Actions          #
    ####################
    if action.upper() == 'TURN_ON':
      payload = '<?xml version="1.0"?>\n' +\
                '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' +\
                '<SOAP-ENV:Body>\n' +\
                '\t<m:SetBinaryState xmlns:m="urn:Belkin:service:basicevent:1">\n' +\
                '<BinaryState>1</BinaryState>\n' +\
                '\t</m:SetBinaryState>\n' +\
                '</SOAP-ENV:Body>\n' +\
                '</SOAP-ENV:Envelope>'
    if action.upper() == 'TURN_OFF':
      payload = '<?xml version="1.0"?>\n' +\
                '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' +\
                '<SOAP-ENV:Body>\n' +\
                '\t<m:SetBinaryState xmlns:m="urn:Belkin:service:basicevent:1">\n' +\
                '<BinaryState>0</BinaryState>\n' +\
                '\t</m:SetBinaryState>\n' +\
                '</SOAP-ENV:Body>\n' +\
                '</SOAP-ENV:Envelope>'
     
    if action.upper() == 'GET_NAME':
      payload = '<?xml version="1.0"?>\n' +\
                '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' +\
                '<SOAP-ENV:Body>\n' +\
                '\t<m:GetFriendlyName xmlns:m="urn:Belkin:service:basicevent:1">\n' +\
                '<FriendlyName></FriendlyName>\n' +\
                '\t</m:GetFriendlyName>\n' +\
                '</SOAP-ENV:Body>\n' +\
                '</SOAP-ENV:Envelope>'

    if action.upper() == 'GET_STATE':
      payload = '<?xml version="1.0"?>\n' +\
                '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">\n' +\
                '<SOAP-ENV:Body>\n' +\
                '\t<m:GetBinaryState xmlns:m="urn:Belkin:service:basicevent:1">\n\n' +\
                '\t</m:GetBinaryState>\n' +\
                '</SOAP-ENV:Body>\n' +\
                '</SOAP-ENV:Envelope>'

    return SOAP, payload
  #}
  # End of WemoBase::get_soap_payload()
  #
  
  #
  # WemoBaseClass::get_friendly_name()
  #{
  def get_friendly_name(self):
  #
  # In some cases, the response from the WeMo will come back in two TCP packets
  # send_to_wemo() only reads the first packet off the wire, which would cause
  # NO_NAME_FOUND, even when the second packet had the data. Now this function
  # will handle all aspects of getting the name, including setting up the TCP
  # connection.
  #
    name = ''
    tries = 0
    MAX_TRIES = 5
    soap_header, payload_data = self.get_soap_payload('GET_FRIEND_NAME', 'GET_NAME')
    message = soap_header + payload_data
    #
    # Setup a socket connection to the device.
    #
    socket.setdefaulttimeout(self.TIMEOUT)
    cmd_addr = get_active_iface_addr((self.LOCAL_GW_ADDR, self.LOCAL_GW_PORT))

    # Wemo commands are sent over TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    # Allow the kernel to reuse the addr without TIME_WAIT expiring
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.connect((self.ip, self.port ))
    sock.sendto( message, (self.ip, self.port ) )
    response = sock.recv(1024)
    while not name and tries < MAX_TRIES:
      name = re.search('<FriendlyName>(.*)</FriendlyName>', response, re.IGNORECASE)
      if name:
          return name.group(1)
      else:
         response = sock.recv(1024)
         tries += 1
    sock.close()
    return 'NO_NAME_FOUND'
  #}
  # End of WemoBaseClass::get_friendly_name()
  #
  
  
  #
  # WemoBaseClass::get_current_state()
  #{
  def get_current_state(self):
  #
  # In some cases, the response from the WeMo will come back in two TCP packets
  # send_to_wemo() only reads the first packet off the wire, which would cause
  # NO_NAME_FOUND, even when the second packet had the data. Now this function
  # will handle all aspects of getting the name, including setting up the TCP
  # connection.
  #
    name = ''
    tries = 0
    MAX_TRIES = 5
    soap_header, payload_data = self.get_soap_payload('GET_BIN_STATE', 'GET_STATE')
    message = soap_header + payload_data
    #
    # Setup a socket connection to the device.
    #
    socket.setdefaulttimeout(self.TIMEOUT)
    cmd_addr = get_active_iface_addr((self.LOCAL_GW_ADDR, self.LOCAL_GW_PORT))

    # Wemo commands are sent over TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
    # Allow the kernel to reuse the addr without TIME_WAIT expiring
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.connect((self.ip, self.port ))
    sock.sendto( message, (self.ip, self.port ) )
    response = sock.recv(1024)
    while not name and tries < MAX_TRIES:
      name = re.search('<BinaryState>(.*)</BinaryState>', response, re.IGNORECASE)
      if name:
        if '1' in name.group(1):
          return 'ON'
        if '0' in name.group(1):
          return 'OFF'
      else:
         response = sock.recv(1024)
         tries += 1
    sock.close()
    return 'NO_STATE_FOUND'
  #}
  # End of WemoBaseClass::get_current_state()
  #
#}
# End of WemoBase Class
#

#
# Wemo Socket class
#{
class WemoSocket(WemoBase):
  """
    WemoSocket class represents Wemo smart socket devices.
  """

  #
  # WemoSocket::turn_on() - Issues the command to turn the socket on.
  #{
  def turn_on(self):
    self.current_state = 'ON'
    soap_header, payload_data = self.get_soap_payload('SET_BIN_STATE','TURN_ON')
    self.send_to_wemo(soap_header + payload_data )
  #}
  # End of WemoSocket::turn_on()
  #
    
  #
  # WemoSocket::turn_off() - Issues the command to turn the socket off.
  #{
  def turn_off(self):
    self.current_state = 'OFF'
    soap_header, payload_data = self.get_soap_payload('SET_BIN_STATE','TURN_OFF')
    self.send_to_wemo(soap_header + payload_data )
  #}
  # End of WemoSocket::turn_off()
  #

  #
  # WemoSocket::toggle() - Issues the command to turn the socket off.
  #{
  def toggle(self):
    if 'ON' in self.current_state:
      self.turn_off()
    elif 'OFF' in self.current_state:
      self.turn_on()
   
  #}
  # End of WemoSocket::toggle()
  #

#}
# End of Wemo Socket class
#

#
# Wemo Sensor class
#{
class WemoSensor(WemoBase):
  """
    WemoSensor class represents Wemo motion sensor devices.
  """
  def check_for_motion(self):
    print "I'm checking for motion!"
    pass
#}
# End of Wemo Sensor class
#

#
# get_active_iface_addr() - returns the interface connected to the
#                           given network.
#{
def get_active_iface_addr( tgt_net ):
  #
  # Hackish way to get the IP address of the active interface. The
  # null_socket is never bound or used, other than to get the address.
  #
  null_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  null_socket.connect((tgt_net[0], tgt_net[1]))
  return null_socket.getsockname()[0]
#}
# End of get_active_iface_addr()
#

#
# find_wemos: sends M-SEARCH requests to check for any Wemo devices on the network.
#             returns a list of tuples in the order (location, uuid, device type)
#             or None.
#{

def find_wemos( dev_type ):
  #
  # Set the Multicast address and port for SSDP
  #
  MULTICAST_ADDR = '239.255.255.250'
  MULTICAST_PORT = 1900
  TIMEOUT = 2.5 # Seconds

  #
  # Define the local gateway IP address so the software can figure out
  # which interface to use.
  #
  LOCAL_GW_ADDR = '192.168.0.1'
  LOCAL_GW_PORT = 80

  #
  # The DISCOVER string is required by the UPnP standard to query for devices.
  # This string is searching SPECIFICALLY for Wemo devices.
  #
  if dev_type.upper() in ["SOCKET",]:
    service_type = 'ST:urn:Belkin:device:controllee:1\r\n'
  elif dev_type.upper() in ["SENSOR",]:
    service_type = 'ST:urn:Belkin:device:sensor:1\r\n'

  # MX (maximum wait time for response in seconds = 2)
  DISCOVER =  'M-SEARCH * HTTP/1.1\r\n' +\
              'HOST:%s:%s\r\n' % (MULTICAST_ADDR, MULTICAST_PORT) +\
              service_type  +\
              'MX:2\r\n'                +\
              'MAN:"ssdp:discover"\r\n\r\n' 
  
  # Set socket timer to TIMEOUT seconds, any blocking operation on sockets will
  # abort if TIMEOUT seconds elapse.
  socket.setdefaulttimeout(TIMEOUT)
  
  loc_addr =  get_active_iface_addr( (LOCAL_GW_ADDR, LOCAL_GW_PORT) )
  
  #
  # Setup and send the MULTICAST request
  #
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # Internet socket using UDP
  
  # Manually change the multicast interface to the chosen one.
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(loc_addr))
  
  # Allow the kernel to reuse the socket even if TIME_WAIT has not expired.
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  
  # Bind the socket to the chosen address and open the multicast port.
  sock.bind((loc_addr, MULTICAST_PORT))
  
  # Ask politely to join the multicast group.
  multicast_request = struct.pack('4sl', socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, multicast_request)
  
  # Send the DISCOVER string to look for Wemos on the network.
  sock.sendto(DISCOVER, (MULTICAST_ADDR, MULTICAST_PORT))
  
  raw_wemos = []
  wemos = []
  found = 0
  
  while True:
    try:
      # Try to receive data from any Wemo devices on the network.
      raw_wemos.append(sock.recv(1024))
    except socket.timeout:
      # When no more Wemos respond within TIMEOUT seconds, then the socket will administratively
      # kill the connection with a timeout exception. 
  
      if found == 0:
        print "Search time (%s seconds) expired, %d device was found." % (TIMEOUT, found)
      break
    found += 1
  
  for wemo in raw_wemos:
    # Search through the device information looking for key data.
    location = re.search(r'location:\s*(.*)', wemo, re.IGNORECASE)
    usn = re.search(r'usn:\s*(.*)', wemo, re.IGNORECASE)
    st  = re.search(r'st:\s*(.*)', wemo, re.IGNORECASE)
  
    if location and usn and st:
      wemo_data = ()
      wemo_data = (location.group(1).strip('\r\n'), 
                   usn.group(1).strip('\r\n'),
                   st.group(1).strip('\r\n'))
  
      if wemo_data not in wemos:
        wemos.append(wemo_data)
  
  if wemos:
    return wemos
  return None
#}
# End of find_wemos()
#
