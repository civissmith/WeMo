#!/usr/bin/python -B
################################################################################
# Copyright (c) 2014 Phil Smith
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
# @Title: client.py
#
# @Author: Phil Smith
#
# @Date: Thu, 25-Dec-14 06:19PM
#
# @Project: New Wemo
#
# @Purpose: Client test app.
#
################################################################################
import os
import socket
import os.path as op

class Client(object):
  """
  Client class for local socket test.
  """

  def __init__(self):
    """
    Initialize structures.
    """
    self.tx_socket = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    self.rx_socket = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    # Transmit to the server input
    self.tx_endpoint = "/tmp/wemo_srv_in"
    # Receive from the server output
    self.rx_endpoint = "/tmp/wemo_srv_out"


  def test_connect(self):

    if not op.exists( self.tx_endpoint ):
      print "Endpoint does not exist."
      return

    self.tx_socket.connect(self.tx_endpoint)
    # Commands will also take the wemo's friendly name
    # e.g. self.tx_socket.send("off_cmd crockpot")
    self.tx_socket.send("on_cmd all")
    self.tx_socket.send("list_cmd")

    raw_data = self.rx_socket.recv( 4096 )
    if raw_data:
      print raw_data


  def connect_rx(self):
    """
    Connects this app to it's rx socket.
    """

    # Socket already in use will return socket.error(98)
    # Get rid of it before trying to connect.
    # Note: must check for 'exists' no 'isfile' because sockets
    #       are not "files".
    if op.exists( self.rx_endpoint ):
      os.remove( self.rx_endpoint )

    self.rx_socket = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )

    try:
      self.rx_socket.bind( self.rx_endpoint )
    except Exception as e:
      print e.args
      print "Could not connect to socket: %s" % self.rx_endpoint
      exit(1)


if __name__ == "__main__":
  cli = Client()
  cli.connect_rx()
  cli.test_connect()
