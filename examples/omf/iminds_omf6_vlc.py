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
#  Testbed : iMinds
#
#     Node
#     node0ZZ 
#     0
#     |
#     |
#     0
#     Node
#     node0ZZ 
#     PING
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
        help="w-iLab.t first reserved node "
            "(must be of form:  "
            " nodex.<experiment_id>.<project_id>.wilab2.ilabt.iminds.be"
            " all letters in lowercase )", 
        type="str")
parser.add_option("-z", "--nodez", dest="nodez", 
        help="w-iLab.t first reserved node "
             "(must be of form:  "
            " nodex.<experiment_id>.<project_id>.wilab2.ilabt.iminds.be"
            " all letters in lowercase )", 
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
ec = ExperimentController(exp_id="iminds_omf6_ping")

# Create and Configure the Nodes

node1 = ec.register_resource("omf::Node")
ec.set(node1, "hostname", nodex)
ec.set(node1, "xmppUser", slicename)
ec.set(node1, "xmppServer", "xmpp.ilabt.iminds.be")
ec.set(node1, "xmppPort", "5222")
ec.set(node1, "xmppPassword", "1234")

iface1 = ec.register_resource("omf::WifiInterface")
ec.set(iface1, "name", "wlan0")
ec.set(iface1, "mode", "adhoc")
ec.set(iface1, "hw_mode", "g")
ec.set(iface1, "essid", "vlc")
ec.set(iface1, "ip", "192.168.0.1/24")
ec.register_connection(iface1, node1)

node2 = ec.register_resource("omf::Node")
ec.set(node2, "hostname", nodez)
ec.set(node2, "xmppUser", slicename)
ec.set(node2, "xmppServer", "xmpp.ilabt.iminds.be")
ec.set(node2, "xmppPort", "5222")
ec.set(node2, "xmppPassword", "1234")

iface2 = ec.register_resource("omf::WifiInterface")
ec.set(iface2, "name", "wlan0")
ec.set(iface2, "mode", "adhoc")
ec.set(iface2, "hw_mode", "g")
ec.set(iface2, "essid", "vlc")
ec.set(iface2, "ip", "192.168.0.2/24")
ec.register_connection(iface2, node2)

channel = ec.register_resource("omf::Channel")
ec.set(channel, "channel", "6")
ec.register_connection(iface1, channel)
ec.register_connection(iface2, channel)

client_ip = "192.168.0.2" 

# Create and Configure the Application
app1 = ec.register_resource("omf::Application")
ec.set(app1, "command", 
    "/root/vlc/vlc-1.1.13/cvlc /root/10-by-p0d.avi --sout '#rtp{dst=%s,port=5004,mux=ts}'" % client_ip) 
ec.register_connection(app1, node1)

## Add a OMFApplication to run the client VLC
app2 = ec.register_resource("omf::Application")
## Send the transmitted video to a file.
ec.set(app2, "command", "/root/vlc/vlc-1.1.13/cvlc rtp://%s:5004 --sout '#standard{access=file,mux=ts,dst=/root/video.ts}'" % client_ip)
ec.register_connection(app2, node2)

## Add a OMFApplication to count the number of bytes in the transmitted video
app3 = ec.register_resource("omf::Application")
## Send the transmitted video to a file.
ec.set(app3, "command", "ls -lah /root/video.ts")
ec.register_connection(app3, node2)

app4 = ec.register_resource("omf::Application")
ec.set(app4, "command", "/usr/bin/killall vlc_app")
ec.register_connection(app4, node1)

app5 = ec.register_resource("omf::Application")
ec.set(app5, "command", "/usr/bin/killall vlc_app")
ec.register_connection(app5, node2)

## start app2 5s after app1
ec.register_condition(app2, ResourceAction.START, app1, ResourceState.STARTED , "5s")
# start app3 after app2 stopped
ec.register_condition(app3, ResourceAction.START, app2, ResourceState.STOPPED , "5s")
# start the kill of vlc processes after they stopped
ec.register_condition(app4, ResourceAction.START, app1, ResourceState.STOPPED , "5s")
ec.register_condition(app5, ResourceAction.START, app2, ResourceState.STOPPED , "5s")

## We need to explicitly STOP all applications
## stop app1 65s after it started
ec.register_condition(app1, ResourceAction.STOP, app1, ResourceState.STARTED , "65s")
## stop app2 5 seconds after app2
ec.register_condition(app2, ResourceAction.STOP, app1, ResourceState.STOPPED , "5s")
# stop app3 after 5s
ec.register_condition(app3, ResourceAction.STOP, app3, ResourceState.STOPPED , "5s")
# stop app4 
ec.register_condition(app4, ResourceAction.STOP, app4, ResourceState.STARTED , "5s")
# stop app5 
ec.register_condition(app5, ResourceAction.STOP, app5, ResourceState.STARTED , "5s")

# Deploy
ec.deploy()

# DO NOT WAIT FOR THE VLC applications or it will never stop
ec.wait_finished([app4, app5])

# Retrieve the bytes transmitted output and print it
byte_count = ec.trace(app3, "stdout")
print "BYTES transmitted", byte_count

# Stop Experiment
ec.shutdown()

