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

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState

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
ec = ExperimentController(exp_id="nitos_omf6_ping")

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
ec.set(iface1, "essid", "ping")
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
ec.set(iface2, "essid", "ping")
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

# Create and Configure the PING Application
app1 = ec.register_resource("omf::Application")
ec.set(app1, "appid", "Ping#1")
ec.set(app1, "command", "/bin/ping -c3 192.168.0.%s" % nodez[-2:])
ec.register_connection(app1, node1)

## Make sure the ping stops after 30 seconds
ec.register_condition(app1, ResourceAction.STOP, app1, 
        ResourceState.STARTED , "30s")

# Deploy
ec.deploy()

ec.wait_finished([app1])

# Retrieve the output of the ping command
ping_output = ec.trace(app1, "stdout")
print "\n PING OUTPUT\n", ping_output, "\n"

# Stop Experiment
ec.shutdown()

