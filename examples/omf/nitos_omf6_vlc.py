#!/usr/bin/env python

###############################################################################
#
#    NEPI, a framework to manage network experiments
#    Copyright (C) 2013 INRIA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Alina Quereilhac <alina.quereilhac@inria.fr>
#         Julien Tribino <julien.tribino@inria.fr>
#
###############################################################################
      
# Topology
#
#
#  Testbed : Nitos
#
#     Node
#     node0XX
#     VLC client
#     0
#     |
#     |
#     0
#     Node
#     node0ZZ 
#     VLC server
#     
#   
#      - Experiment:
#        - t0 : Deployment
#        - t1 : Ping Start
#        - t2 (t1 + 10s) : Ping stop
#        - t3 (t2 + 2s) : Kill the application
#

from nepi.execution.resource import ResourceAction, ResourceState
from nepi.execution.ec import ExperimentController

from optparse import OptionParser
import os

usage = ("usage: %prog -x <nodex> -z <nodez> -s <slice-name> -c <channel>")

parser = OptionParser(usage = usage)
parser.add_option("-x", "--nodex", dest="nodex", 
        help="Nitos first reserved node "
            "(e.g. hostname must be of form: node0XX)", 
        type="str")
parser.add_option("-z", "--nodez", dest="nodez", 
        help="Nitos second reserved node "
            "(e.g. hostname must be of form: node0ZZ)", 
        type="str")
parser.add_option("-c", "--channel", dest="channel", 
        help="Nitos reserved channel",
        type="str")
parser.add_option("-s", "--slice-name", dest="slicename", 
        help="Nitos slice name", type="str")
(options, args) = parser.parse_args()

nodex = options.nodex
nodez = options.nodez
slicename = options.slicename
chan = options.channel

# Create the EC
ec = ExperimentController(exp_id="nitos_omf6_vlc")

# Create and Configure the Nodes
node1 = ec.register_resource("omf::Node")
ec.set(node1, "hostname", nodex)
ec.set(node1, "xmppUser", slicename)
ec.set(node1, "xmppServer", "nitlab.inf.uth.gr")
ec.set(node1, "xmppPort", "5222")
ec.set(node1, "xmppPassword", "1234")

# Create and Configure the Interfaces
iface1 = ec.register_resource("omf::WifiInterface")
ec.set(iface1, "name", "wlan0")
ec.set(iface1, "mode", "adhoc")
ec.set(iface1, "hw_mode", "g")
ec.set(iface1, "essid", "vlc")
ec.set(iface1, "ip", "192.168.0.%s/24" % nodex[-2:]) 
ec.register_connection(node1, iface1)

# Create and Configure the Nodes
node2 = ec.register_resource("omf::Node")
ec.set(node2, "hostname", nodez)
ec.set(node2, "xmppUser", slicename)
ec.set(node2, "xmppServer", "nitlab.inf.uth.gr")
ec.set(node2, "xmppPort", "5222")
ec.set(node2, "xmppPassword", "1234")

# Create and Configure the Interfaces
iface2 = ec.register_resource("omf::WifiInterface")
ec.set(iface2, "name", "wlan0")
ec.set(iface2, "mode", "adhoc")
ec.set(iface2, "hw_mode", "g")
ec.set(iface2, "essid", "vlc")
ec.set(iface2, "ip", "192.168.0.%s/24" % nodez[-2:]) 
ec.register_connection(node2, iface2)

# Create and Configure the Channel
channel = ec.register_resource("omf::Channel")
ec.set(channel, "channel", chan)
ec.set(channel, "xmppUser", slicename)
ec.set(channel, "xmppServer", "nitlab.inf.uth.gr")
ec.set(channel, "xmppPort", "5222")
ec.set(channel, "xmppPassword", "1234")
ec.register_connection(iface1, channel)
ec.register_connection(iface2, channel)

client_ip = "192.168.0.%s" % nodez[-2:]

# Create and Configure the Application
app1 = ec.register_resource("omf::Application")
ec.set(app1, "command", 
    "DISPLAY=localhost:10.0 XAUTHORITY=/root/.Xauthority /root/vlc/vlc-1.1.13/cvlc /root/10-by-p0d.avi --sout '#rtp{dst=%s,port=5004,mux=ts}'" % client_ip) 
ec.register_connection(app1, node1)

## Add a OMFApplication to run the client VLC and count the numer of bytes 
## transmitted,  using wc.
app2 = ec.register_resource("omf::Application")
ec.set(app2, "command", 
    "DISPLAY=localhost:10.0 XAUTHORITY=/root/.Xauthority /root/vlc/vlc-1.1.13/cvlc rtp://%s:5004 | wc -c "% client_ip)

## Alternativelly, you can try to send the video to standard output and 
## recover it using the stdout trace. However, it seems that sending 
## binary messages back to the client is not well supported by the OMF 6 RC
#ec.set(app2, "command", "DISPLAY=localhost:10.0 XAUTHORITY=/root/.Xauthority /root/vlc/vlc-1.1.13/cvlc rtp://%s:5004 --sout '#standard{access=file,mux=ts,dst=-}'" % client_ip)
ec.register_connection(app2, node2)

## stop app1 65s after it started
ec.register_condition(app1, ResourceAction.STOP, app1, ResourceState.STARTED , "65s")
## start app2 5s after app1
ec.register_condition(app2, ResourceAction.START, app1, ResourceState.STARTED , "5s")
## stop app2 5 seconds after app2
ec.register_condition(app2, ResourceAction.STOP, app1, ResourceState.STOPPED , "5s")

# Deploy
ec.deploy()

ec.wait_finished([app2])

# Retrieve the bytes transmitted count and print it
byte_count = ec.trace(app2, "stdout")
print "BYTES transmitted", byte_count

## If you redirected the video to standard output, you can try to 
## retrieve the stdout of the VLC client
## video = ec.trace(app2, "stdout")
#f = open("video.ts", "w")
#f.write(video)
#f.close()

# Stop Experiment
ec.shutdown()

