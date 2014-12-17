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

import ipaddr
import random
import re

########## Declaration of resources #####################################

def add_linux_node(ec):
    node = ec.register_resource("linux::Node")
    ec.set(node, "hostname", "localhost")
    ec.set(node, "cleanProcesses", True)

    return node

def add_node(ec, simu):
    node = ec.register_resource("ns3::Node")
    ec.set(node, "enableStack", True)
    ec.register_connection(node, simu)

    return node

def add_device(ec, node, ip, prefix):
    dev = ec.register_resource("ns3::CsmaNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)
    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

def add_ping_app(ec, node, remote_ip):
    app = ec.register_resource("ns3::V4Ping")
    ec.set (app, "Remote", remote_ip)
    ec.set (app, "Verbose", True)
    ec.set (app, "Interval", "1s")
    ec.set (app, "StartTime", "0s")
    ec.set (app, "StopTime", "20s")
    ec.register_connection(app, node)

    return app

############## Experiment design and execution ################################

def make_experiment(node_count, app_count, opdelay, delay):

    ResourceManager._reschedule_delay = "%0.1fs" % delay

    # Create Experiment Controller:
    ec = ExperimentController("ns3_bench")

    # Add the physical host in which to run the simulation
    lnode = add_linux_node(ec)

    # Add a simulation resource
    simu = ec.register_resource("linux::ns3::Simulation")
    ec.set(simu, "verbose", True)
    ec.register_connection(simu, lnode)

    # Add simulated nodes and applications
    nodes = list()
    apps = list()
    devs = list()
    ips = dict()

    prefix = "16"
    base_addr = "10.0.0.0/%s" % prefix
    net = ipaddr.IPv4Network(base_addr)
    host_itr = net.iterhosts()

    for i in xrange(node_count):
        node = add_node(ec, simu)
        nodes.append(node)
        
        ip = host_itr.next()
        ip = ip.exploded
        dev = add_device(ec, node, ip, prefix)
        devs.append(dev)

        ips[node] = ip

    for nid in nodes:
        for j in xrange(app_count):
            # If there is only one node, ping itself. If there are more
            # choose one target randomly.
            remote_ip = ips[nid]
            
            if len(nodes) > 1:
                choices = ips.values()
                choices.remove(remote_ip)
                remote_ip = random.choice(choices)

            app = add_ping_app(ec, node, remote_ip)
            apps.append(app)

    chan = ec.register_resource("ns3::CsmaChannel")
    ec.set(chan, "Delay", "0s")

    for dev in devs:
        ec.register_connection(chan, dev)

    return (ec, apps, nodes + apps + devs)

def validate(ec, apps, wait_rms):
    # Validate that there was no packet loss
    simu = ec.filter_resources("linux::ns3::Simulation")
    stdout = ec.trace(simu[0],"stdout")

    _reloss = re.compile("(?P<loss>\d+)% packet loss")
    losses = _reloss.findall(stdout)
    #if not losses or filter(lambda loss: int(loss) > 90, losses):
    if not losses:
        raise RuntimeError(stdout)


