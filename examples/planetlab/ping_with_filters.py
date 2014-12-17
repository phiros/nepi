#!/usr/bin/env python
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
# Author: Lucia Guevgeozian <lucia.guevgeozian_odizzio@inria.fr>

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/planetlab/ping_with_filters.py -s <pl-slice> -u <pl-user> -p <pl-password> -k <pl-ssh-key>  

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState

from optparse import OptionParser
import os


def create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, 
       hostname = None, country = None, operatingSystem = None, 
       minBandwidth = None, minCpu = None):

    node = ec.register_resource("planetlab::Node")

    ec.set(node, "username", pl_slice)
    ec.set(node, "identity", pl_ssh_key)
    ec.set(node, "pluser", pl_user)
    ec.set(node, "plpassword", pl_password)

    if hostname:
        ec.set(node, "hostname", hostname)
    if country:
        ec.set(node, "country", country)
    if operatingSystem:
        ec.set(node, "operatingSystem", operatingSystem)
    if minBandwidth:
        ec.set(node, "minBandwidth", minBandwidth)
    if minCpu:
        ec.set(node, "minCpu", minCpu)

    ec.set(node, "cleanExperiment", True)
    ec.set(node, "cleanProcesses", True)
    
    return node

def add_app(ec, command, node, newname = None, sudo = None, 
        video = None, depends = None, forward_x11 = None, env = None):
    app = ec.register_resource("linux::Application")

    if sudo is not None:
        ec.set(app, "sudo", sudo)
    if video is not None:
        ec.set(app, "sources", video)
    if depends is not None:
        ec.set(app, "depends", depends)
    if forward_x11 is not None:
        ec.set(app, "forwardX11", forward_x11)
    if env is not None:
        ec.set(app, "env", env)

    ec.set(app, "command", command)

    ec.register_connection(app, node)

    # add collector to download application standar output
    collector = ec.register_resource("Collector")
    ec.set(collector, "traceName", "stdout")
    if newname:
        ec.set(collector, "rename", newname)
    ec.register_connection(app, collector)

    return app

usage = ("usage: %prog -s <pl-slice> -u <pl-user> -p <pl-password> "
    "-k <pl-ssh-key> -c <country> -o <operating-system> -H <hostname> ")

parser = OptionParser(usage = usage)
parser.add_option("-s", "--pl-slice", dest="pl_slice",
        help="PlanetLab slicename", type="str")
parser.add_option("-u", "--pl-user", dest="pl_user",
        help="PlanetLab web username", type="str")
parser.add_option("-p", "--pl-password", dest="pl_password",
        help="PlanetLab web password", type="str")
parser.add_option("-k", "--pl-ssh-key", dest="pl_ssh_key",
        help="Path to private SSH key associated with the PL account",
        type="str")
parser.add_option("-c", "--country", dest="country",
        help="Country for the PL hosts",
        type="str")
parser.add_option("-o", "--os", dest="os",
        help="Operating system for the PL hosts", default="f14",
        type="str")
parser.add_option("-H", "--hostname", dest="hostname",
        help="PlanetLab hostname",
        type="str")

(options, args) = parser.parse_args()

pl_slice = options.pl_slice
pl_ssh_key = options.pl_ssh_key
pl_user = options.pl_user
pl_password = options.pl_password
hostname = options.hostname
country = options.country
os = options.os

# Create the entity Experiment Controller:
ec = ExperimentController("pl_ping_filters")

# Register the nodes resources:

# Choose the PlanetLab nodes for the experiment, in this example 5 nodes are
# used, and they are picked according to different criterias.

# First node will be the one defined by its hostname.
node1 = create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, 
        hostname = hostname)

# Second node will be any node in the selected country.
node2 = create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, 
        country=country)

# Third node will be a node in the selected country and with the selected
# fedora OS
node3 = create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, 
        country = country,
        operatingSystem = os)

# Forth node will have at least 50% of CPU available
minCpu=50
node4 = create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, 
        minCpu = minCpu)

# Fifth node can be any node, constrains are not important.
node5 = create_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password)

# Register the applications to run in the nodes, in this case just ping to the 
# first node:
apps = []
for node in [node2, node3, node4, node5]:
    command = "ping -c5 %s" % hostname
    trace_name = "%s.ping" % hostname
    app = add_app(ec, command, node, newname = trace_name)
    apps.append(app)

# Register conditions

# The nodes that are completely identified by their hostnames have to be provisioned 
# before the rest of the nodes. This assures that no other resource will use the
# identified node even if the constraints matchs. 
# In this example node2, node3, node4 and node5, are deployed after node1 is 
# provisioned. node1 must be the node hostname, meanwhile node2, node3,
# node4 and node5 just need to fulfill certain constraints.
# Applications are always deployed after nodes, so no need to register conditions
# for the apps in this example.

ec.register_condition(node2, ResourceAction.DEPLOY, node1, ResourceState.PROVISIONED)
ec.register_condition(node3, ResourceAction.DEPLOY, node1, ResourceState.PROVISIONED)
ec.register_condition(node4, ResourceAction.DEPLOY, node1, ResourceState.PROVISIONED)
ec.register_condition(node5, ResourceAction.DEPLOY, node1, ResourceState.PROVISIONED)
    
# Deploy the experiment:
ec.deploy()

# Wait until the applications are finish to retrive the traces:
ec.wait_finished(apps)

print "Results stored at", ec.exp_dir

# Do the experiment controller shutdown:
ec.shutdown()

# END
