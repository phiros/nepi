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
        clsinit_copy, ResourceAction, ResourceFactory

import time

wait_time = 0

class Link(ResourceManager):
    _rtype = "dummy::Link"

    def do_deploy(self):
        time.sleep(wait_time)
        super(Link, self).do_deploy()
        self.logger.debug(" -------- DEPLOYED ------- ")

class Interface(ResourceManager):
    _rtype = "dummy::Interface"

    def do_deploy(self):
        node = self.get_connected(Node.get_rtype())[0]
        link = self.get_connected(Link.get_rtype())[0]

        if node.state < ResourceState.READY or \
                link.state < ResourceState.READY:
            self.ec.schedule(self.reschedule_delay, self.deploy)
            self.logger.debug(" -------- RESCHEDULING ------- ")
        else:
            time.sleep(wait_time)
            super(Interface, self).do_deploy()
            self.logger.debug(" -------- DEPLOYED ------- ")

class Node(ResourceManager):
    _rtype = "dummy::Node"

    def do_deploy(self):
        self.logger.debug(" -------- DO_DEPLOY ------- ")
        time.sleep(wait_time)
        super(Node, self).do_deploy()
        self.logger.debug(" -------- DEPLOYED ------- ")

class Application(ResourceManager):
    _rtype = "dummy::Application"

    def do_deploy(self):
        node = self.get_connected(Node.get_rtype())[0]

        if node.state < ResourceState.READY: 
            self.ec.schedule(self.reschedule_delay, self.deploy)
            self.logger.debug(" -------- RESCHEDULING ------- ")
        else:
            time.sleep(wait_time)
            super(Application, self).do_deploy()
            self.logger.debug(" -------- DEPLOYED ------- ")

    def do_start(self):
        super(Application, self).do_start()
        time.sleep(wait_time)
        self.ec.schedule("0s", self.stop)

ResourceFactory.register_type(Application)
ResourceFactory.register_type(Node)
ResourceFactory.register_type(Interface)
ResourceFactory.register_type(Link)

############## Experiment design and execution ################################

def make_experiment(node_count, app_count, opdelay, delay):
    global wait_time
    wait_time = opdelay
    ResourceManager._reschedule_delay = "%0.1fs" % delay

    # Create Experiment Controller:
    ec = ExperimentController("dummy_bench")
            
    # Add simulated nodes and applications
    nodes = list()
    apps = list()
    ifaces = list()

    for i in xrange(node_count):
        node = ec.register_resource("dummy::Node")
        nodes.append(node)
        
        iface = ec.register_resource("dummy::Interface")
        ec.register_connection(node, iface)
        ifaces.append(iface)

        for i in xrange(app_count):
            app = ec.register_resource("dummy::Application")
            ec.register_connection(node, app)
            apps.append(app)

    link = ec.register_resource("dummy::Link")

    for iface in ifaces:
        ec.register_connection(link, iface)

    return (ec, apps, nodes + apps + ifaces)

def validate(ec, apps, wait_rms):
    pass


