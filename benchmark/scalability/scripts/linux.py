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
# Author: Alina Quereilhac <alina.quereilhac@inria.fr>

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceManager, ResourceState, \
        clsinit_copy, ResourceAction

import os
import re
import random

########## Declaration of resources #####################################

def add_node(ec, hostname):
    username = os.environ.get("PL_SLICE")
    identity = os.environ.get("PL_SSHKEY")

    node = ec.register_resource("linux::Node")
    ec.set(node, "hostname", hostname)
    ec.set(node, "username", username)
    ec.set(node, "identity", identity)
    ec.set(node, "cleanProcesses", True)
    return node

def add_app(ec, node, hostname):
    command = "ping -c3 %s" % hostname
    app = ec.register_resource("linux::Application")
    ec.set(app, "command", command)
    ec.register_connection(app, node)
    return app

############## Experiment design and execution ################################

def make_experiment(node_count, app_count, opdelay, delay):

    ResourceManager._reschedule_delay = "%0.1fs" % delay

    hostnames = []
    with open("planetlab_hosts.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            hostnames.append(line)

    # Create Experiment Controller:
    ec = ExperimentController("linux_bench")

    nodes = []
    apps = []

    for i in xrange(node_count):
        hostname = hostnames[i] 
        node = add_node(ec, hostname)
        nodes.append(node)
        
    i = 0
    for nid in nodes:
        for j in xrange(app_count):
            # If there is only one node, ping itself. If there are more
            # choose one target randomly.
            hostname = hostnames[i]
            
            if len(nodes) > 1:
                choices = hostnames[:]
                choices.remove(hostname)
                hostname = random.choice(choices)

            app = add_app(ec, node, hostname)
            apps.append(app)

        i+=1

    return (ec, apps, nodes + apps)

def validate(ec, apps, wait_rms):
    # Validate that there was no packet loss
    _reloss = re.compile("(?P<loss>\d+)% packet loss")
    
    for app in apps:
        rm = ec.get_resource(app)
        stdout = ec.trace(app,"stdout")
        m = _reloss.search(stdout)

        # A packet loss over 90 is considered as an error
        #if not m or int(m.groupdict()["loss"]) > 90:
        if not m:
            raise RuntimeError(stdout)

