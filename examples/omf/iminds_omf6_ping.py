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
parser.add_option("-s", "--slice-name", dest="slicename", 
        help="Nitos slice name", type="str")
(options, args) = parser.parse_args()

nodex = options.nodex
nodez = options.nodez
slicename = options.slicename

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
ec.set(iface1, "essid", "ping")
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
ec.set(iface2, "essid", "ping")
ec.set(iface2, "ip", "192.168.0.2/24")
ec.register_connection(iface2, node2)

channel = ec.register_resource("omf::Channel")
ec.set(channel, "channel", "6")
ec.register_connection(iface1, channel)
ec.register_connection(iface2, channel)

# Create and Configure the Application
app1 = ec.register_resource("omf::Application")
ec.set(app1, "command", "ping -c3 192.168.0.2") 
ec.register_connection(app1, node1)

## Make sure the ping stops after 30 seconds
ec.register_condition(app1, ResourceAction.STOP, app1, 
        ResourceState.STARTED , "30s")

# Deploy
ec.deploy()

# Wait until the VLC client is finished
ec.wait_finished([app1])

# Retrieve the output of the ping command
ping_output = ec.trace(app1, "stdout")
print "\n PING OUTPUT\n", ping_output, "\n"

# Stop Experiment
ec.shutdown()

