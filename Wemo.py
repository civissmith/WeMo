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

# Wemo {
class Wemo(object):
    """
    Represents the basic Wemo device. This class is the base for all other
    Wemo devices.
    """

    timeout = 2.5

    def __init__(self, url=''):
        """
        Initialize the Wemo base class.
        """

        # Strip off the trailing slash since the commands need to have a leading slash.
        if url[-1] == '/':
             self.url = url[:-1]
        else:
             self.url = url

        # Strip out the URL information to get the IP address and port.
        self.ip, self.port = url.strip('http://').strip('/setup.xml').split(':')
        self.port = int(self.port)
        self.name = self.get_friendly_name()
        self.current_state = self.get_current_state()

    def __str__(self):
        """
        String representation of the Wemo class.
        """
        dev_str = "%s - %s:%s" % ( self.name, self.ip, self.port )
        return dev_str


    def send_to_wemo(self, message):
        """
        Sends the SOAP and payload message to the Wemo and returns the data received from
        the device.
        """
        #
        # Setup a socket connection to the device.
        #
        socket.setdefaulttimeout(Wemo.timeout)

        # Wemo commands are sent over TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        # Allow the kernel to reuse the addr without TIME_WAIT expiring
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.connect((self.ip, self.port))
        sock.sendto(message, (self.ip, self.port))
        response = sock.recv(1024)
        sock.close()
        return response

    # get_soap_payload(){
    def get_soap_payload(self, service, action):
        """
        Returns a SOAP header and payload to send to a Wemo.
        """

        # TODO: Move the XML data to template files.
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
    #} End of get_soap_payload()

    # get_friendly_name(){
    def get_friendly_name(self):
        """
        Returns the "friendly name" of the Wemo.
        """
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
        socket.setdefaulttimeout(Wemo.timeout)

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
    #} End of get_friendly_name()

    # get_current_state(){
    def get_current_state(self):
        """
        Returns the current state of the Wemo device.
        """
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
        # TODO: Setup a socket factory to return configured sockets
        socket.setdefaulttimeout(Wemo.timeout)

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
    #} End of get_current_state()


    @staticmethod
    def get_active_iface_addr():
        """
        Hackish way to get the IP address of the active interface. The
        null_socket is never bound or used, other than to get the address.
        """
        eth_dev = Wemo.detect_active_iface()
        if eth_dev not in 'NO_IF':
            null_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(null_socket.fileno(), 0x8915, struct.pack('256s', eth_dev[:15]))[20:24])
        return '127.0.0.1'


    # find_wemos(){
    @staticmethod
    def find_wemos(dev_type):
        """
        Find the WeMo devices on the network.
        """
        #
        # Set the Multicast address and port for SSDP
        #
        MULTICAST_ADDR = '239.255.255.250'
        MULTICAST_PORT = 1900

        devices = { "SOCKET": 'ST:urn:Belkin:device:controllee:1\r\n',
                    "SENSOR": 'ST:urn:Belkin:device:sensor:1\r\n',
                    "LINK"  : 'ST:urn:Belkin:device:bridge:1\r\n',
                  }
        if dev_type.upper() in devices:
           service_type = devices[dev_type.upper()]
        else:
            return []

        # MX (maximum wait time for response in seconds = 2)
        DISCOVER =    'M-SEARCH * HTTP/1.1\r\n' +\
                                'HOST:%s:%s\r\n' % (MULTICAST_ADDR, MULTICAST_PORT) +\
                                service_type    +\
                                'MX:2\r\n'                                +\
                                'MAN:"ssdp:discover"\r\n\r\n'

        # Set socket timer to TIMEOUT seconds, any blocking operation on sockets will
        # abort if TIMEOUT seconds elapse.
        socket.setdefaulttimeout(Wemo.timeout)

        loc_addr = Wemo.get_active_iface_addr()

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
                break
            found += 1

        for wemo in raw_wemos:
            # Search through the device information looking for key data.
            url_found = re.search(r'location:\s*(.*)', wemo, re.IGNORECASE)

            if url_found:
                wemo_data = url_found.group(1).strip('\r\n')

                if wemo_data not in wemos:
                    wemos.append(wemo_data)

        if wemos:
            return wemos
        return []
    #} End of find_wemos()


    @staticmethod
    def detect_active_iface():
       """
       Uses /proc/net/dev to determine which Ethernet interface to use. Returns the device's
       name (such as 'eth0', 'wlan0', or whatever is appropriate.
       """
       net_file = open('/proc/net/dev', 'r')
       # These are the first fields in rows we're not interested in.
       rejects = ['Inter-|', 'face', 'lo:']
       for line in net_file:
           data = line.split()
           if data[0] in rejects:
               continue
           # Chop the ':' from the device name.
           name = data[0][:-1]
           # Check for a interface that has transmitted.
           tx_bytes = int(data[9])
           if tx_bytes > 0:
               return name
       return 'NO_IF'

#} End of Wemo Class



# Wemo Socket class {
class Socket(Wemo):
    """
    Socket class represents Wemo smart socket devices.
    """

    def turn_on(self):
        """
        Sets the current_state and sends the command to turn the socket ON.
        """
        self.current_state = 'ON'
        soap_header, payload_data = self.get_soap_payload('SET_BIN_STATE','TURN_ON')
        self.send_to_wemo(soap_header + payload_data )


    def turn_off(self):
        """
        Sets the current_state and sends the command to turn the socket OFF.
        """
        self.current_state = 'OFF'
        soap_header, payload_data = self.get_soap_payload('SET_BIN_STATE','TURN_OFF')
        self.send_to_wemo(soap_header + payload_data )

    def toggle(self):
        """
        Checks the current_state and either sends an ON or OFF command.
        """
        if 'ON' in self.current_state:
            self.turn_off()
        elif 'OFF' in self.current_state:
            self.turn_on()

    @staticmethod
    def find_wemos():
        """
        Extends the base version to look specifically for sockets.
        """
        return super(Socket, Socket).find_wemos("SOCKET")

#} End of Wemo Socket class



# Wemo Sensor class {
class Sensor(Wemo):
    """
    Sensor class represents Wemo motion sensor devices.
    """
    def check_for_motion(self):
        print "I'm checking for motion!"

    @staticmethod
    def find_wemos():
        """
        Extends the base version to look specifically for sockets.
        """
        return super(Sensor, Sensor).find_wemos("SENSOR")

#} End of Wemo Sensor class


# Wemo Link class {
class Link(Wemo):

    # TODO: Merge in WemoPOC's Link class methods. (After socket factory)

    @staticmethod
    def find_wemos():
        """
        Extends the base version to look specifically for sockets.
        """
        return super(Link, Link).find_wemos("LINK")

#} End of Wemo Link class
