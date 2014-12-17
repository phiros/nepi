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


from nepi.execution.attribute import Attribute
from nepi.execution.ec import ExperimentController, FailureLevel 
from nepi.execution.resource import ResourceManager, ResourceState, \
        clsinit_copy, ResourceAction

import random
import time
import unittest

@clsinit_copy
class MyResource(ResourceManager):
    _rtype = "MyResource"

    @classmethod
    def _register_attributes(cls):
        cool_attr = Attribute("my_attr", "is a really nice attribute!")
        cls._register_attribute(cool_attr)

    def __init__(self, ec, guid):
        super(MyResource, self).__init__(ec, guid)

@clsinit_copy
class AnotherResource(ResourceManager):
    _rtype = "AnotherResource"

    def __init__(self, ec, guid):
        super(AnotherResource, self).__init__(ec, guid)

class Channel(ResourceManager):
    _rtype = "Channel"

    def __init__(self, ec, guid):
        super(Channel, self).__init__(ec, guid)

    def do_deploy(self):
        time.sleep(1)
        super(Channel, self).do_deploy()
        self.logger.debug(" -------- DEPLOYED ------- ")
       
class Interface(ResourceManager):
    _rtype = "Interface"

    def __init__(self, ec, guid):
        super(Interface, self).__init__(ec, guid)

    def do_deploy(self):
        node = self.get_connected(Node.get_rtype())[0]
        chan = self.get_connected(Channel.get_rtype())[0]

        if node.state < ResourceState.PROVISIONED:
            self.ec.schedule("0.5s", self.deploy)
        elif chan.state < ResourceState.READY:
            self.ec.schedule("0.5s", self.deploy)
        else:
            time.sleep(2)
            super(Interface, self).do_deploy()
            self.logger.debug(" -------- DEPLOYED ------- ")

class Node(ResourceManager):
    _rtype = "Node"

    def __init__(self, ec, guid):
        super(Node, self).__init__(ec, guid)

    def do_deploy(self):
        if self.state == ResourceState.NEW:
            self.do_discover()
            self.do_provision()
            self.logger.debug(" -------- PROVISIONED ------- ")
            self.ec.schedule("1s", self.deploy)
        elif self.state == ResourceState.PROVISIONED:
            ifaces = self.get_connected(Interface.get_rtype())
            for rm in ifaces:
                if rm.state < ResourceState.READY:
                    self.ec.schedule("0.5s", self.deploy)
                    return 

            super(Node, self).do_deploy()
            self.logger.debug(" -------- DEPLOYED ------- ")

class Application(ResourceManager):
    _rtype = "Application"

    def __init__(self, ec, guid):
        super(Application, self).__init__(ec, guid)

    def do_deploy(self):
        node = self.get_connected(Node.get_rtype())[0]
        if node.state < ResourceState.READY:
            self.ec.schedule("0.5s", self.deploy)
        else:
            time.sleep(random.random() * 2)
            super(Application, self).do_deploy()
            self.logger.debug(" -------- DEPLOYED ------- ")

    def do_start(self):
        super(Application, self).do_start()
        time.sleep(random.random() * 3)
        self.ec.schedule("0.5s", self.stop)

class ErrorApplication(ResourceManager):
    _rtype = "ErrorApplication"

    def __init__(self, ec, guid):
        super(ErrorApplication, self).__init__(ec, guid)

    def do_deploy(self):
        node = self.get_connected(Node.get_rtype())[0]
        if node.state < ResourceState.READY:
            self.ec.schedule("0.5s", self.deploy)
        else:
            time.sleep(random.random() * 2)
            raise RuntimeError, "NOT A REAL ERROR. JUST TESTING"

class ResourceFactoryTestCase(unittest.TestCase):
    def test_add_resource_factory(self):
        from nepi.execution.resource import ResourceFactory

        ResourceFactory._resource_types = dict()
        ResourceFactory.register_type(MyResource)
        ResourceFactory.register_type(AnotherResource)

        # Take into account default 'Critical' attribute
        self.assertEquals(MyResource.get_rtype(), "MyResource")
        self.assertEquals(len(MyResource._attributes), 3)

        self.assertEquals(ResourceManager.get_rtype(), "Resource")
        self.assertEquals(len(ResourceManager._attributes), 2)

        self.assertEquals(AnotherResource.get_rtype(), "AnotherResource")
        self.assertEquals(len(AnotherResource._attributes), 2)

        self.assertEquals(len(ResourceFactory.resource_types()), 2)
        
        # restore factory state for other tests
        from nepi.execution.resource import populate_factory
        ResourceFactory._resource_types = dict()
        populate_factory()

class ResourceManagerTestCase(unittest.TestCase):
    def test_register_condition(self):
        ec = ExperimentController()
        rm = ResourceManager(ec, 15)

        group = [1,3,5,7]
        rm.register_condition(ResourceAction.START, group,
                ResourceState.STARTED)

        group = [10,8]
        rm.register_condition(ResourceAction.START,
                group, ResourceState.STARTED, time = "10s")

        waiting_for = []
        conditions = rm.conditions.get(ResourceAction.START)
        for (group, state, time) in conditions:
            waiting_for.extend(group)

        self.assertEquals(waiting_for, [1, 3, 5, 7, 10, 8])

        group = [1, 2, 3, 4, 6]
        rm.unregister_condition(group)

        waiting_for = []
        conditions = rm.conditions.get(ResourceAction.START)
        for (group, state, time) in conditions:
            waiting_for.extend(group)

        self.assertEquals(waiting_for, [5, 7, 10, 8])

    def test_deploy_in_order(self):
        """
        Test scenario: 2 applications running one on 1 node each. 
        Nodes are connected to Interfaces which are connected
        through a channel between them.

         - Application needs to wait until Node is ready to be ready
         - Node needs to wait until Interface is ready to be ready
         - Interface needs to wait until Node is provisioned to be ready
         - Interface needs to wait until Channel is ready to be ready
         - The channel doesn't wait for any other resource to be ready

        """
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(Application)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)
        ResourceFactory.register_type(Channel)

        ec = ExperimentController()

        app1 = ec.register_resource("Application")
        app2 = ec.register_resource("Application")
        node1 = ec.register_resource("Node")
        node2 = ec.register_resource("Node")
        iface1 = ec.register_resource("Interface")
        iface2 = ec.register_resource("Interface")
        chan = ec.register_resource("Channel")

        ec.register_connection(app1, node1)
        ec.register_connection(app2, node2)
        ec.register_connection(iface1, node1)
        ec.register_connection(iface2, node2)
        ec.register_connection(iface1, chan)
        ec.register_connection(iface2, chan)

        ec.deploy()

        guids = [app1, app2]
        ec.wait_finished(guids)

        ec.shutdown()

        rmapp1 = ec.get_resource(app1)
        rmapp2 = ec.get_resource(app2)
        rmnode1 = ec.get_resource(node1)
        rmnode2 = ec.get_resource(node2)
        rmiface1 = ec.get_resource(iface1)
        rmiface2 = ec.get_resource(iface2)
        rmchan = ec.get_resource(chan)

        ## Validate deploy order
        # - Application needs to wait until Node is ready to be ready
        self.assertTrue(rmnode1.ready_time < rmapp1.ready_time)
        self.assertTrue(rmnode2.ready_time < rmapp2.ready_time)

        # - Node needs to wait until Interface is ready to be ready
        self.assertTrue(rmnode1.ready_time > rmiface1.ready_time)
        self.assertTrue(rmnode2.ready_time > rmiface2.ready_time)

        # - Interface needs to wait until Node is provisioned to be ready
        self.assertTrue(rmnode1.provision_time < rmiface1.ready_time)
        self.assertTrue(rmnode2.provision_time < rmiface2.ready_time)

        # - Interface needs to wait until Channel is ready to be ready
        self.assertTrue(rmchan.ready_time < rmiface1.ready_time)
        self.assertTrue(rmchan.ready_time < rmiface2.ready_time)

    def test_concurrency(self):
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(Application)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)
        ResourceFactory.register_type(Channel)

        ec = ExperimentController()

        node = ec.register_resource("Node")

        apps = list()
        for i in xrange(1000):
            app = ec.register_resource("Application")
            ec.register_connection(app, node)
            apps.append(app)

        ec.deploy()

        ec.wait_finished(apps)
        
        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(
               all([ec.state(guid) == ResourceState.STOPPED \
                for guid in apps])
                )

        ec.shutdown()

    def test_exception(self):
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(ErrorApplication)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)

        ec = ExperimentController()

        node = ec.register_resource("Node")

        app = ec.register_resource("ErrorApplication")
        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished(app)

        ec.shutdown()

        self.assertEquals(ec._fm._failure_level, FailureLevel.RM_FAILURE)

    def test_critical(self):
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(ErrorApplication)
        ResourceFactory.register_type(Application)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)

        ec = ExperimentController()

        node = ec.register_resource("Node")

        apps = list()
        
        eapp = ec.register_resource("ErrorApplication")
        ec.set(eapp, "critical", False)
        ec.register_connection(eapp, node)
        apps.append(eapp)

        for i in xrange(10):
            app = ec.register_resource("Application")
            ec.register_connection(app, node)
            apps.append(app)

        ec.deploy()

        ec.wait_finished(apps)
        
        state = ec.state(eapp)
        self.assertEquals(state, ResourceState.FAILED)
      
        apps.remove(eapp)

        for app in apps:
            state = ec.state(app)
            self.assertEquals(state, ResourceState.STOPPED)
        
        ec.shutdown()

        self.assertEquals(ec._fm._failure_level, FailureLevel.OK)

    def test_start_with_condition(self):
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(Application)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)

        ec = ExperimentController()

        node = ec.register_resource("Node")

        app1 = ec.register_resource("Application")
        ec.register_connection(app1, node)

        app2 = ec.register_resource("Application")
        ec.register_connection(app2, node)

        ec.register_condition(app2, ResourceAction.START, app1, 
                ResourceState.STARTED, time = "5s")

        ec.deploy()

        ec.wait_finished([app1, app2])
        
        rmapp1 = ec.get_resource(app1)
        rmapp2 = ec.get_resource(app2)

        self.assertTrue(rmapp2.start_time > rmapp1.start_time)
        
        ec.shutdown()

    def test_stop_with_condition(self):
        from nepi.execution.resource import ResourceFactory
        
        ResourceFactory.register_type(Application)
        ResourceFactory.register_type(Node)
        ResourceFactory.register_type(Interface)

        ec = ExperimentController()

        node = ec.register_resource("Node")

        app1 = ec.register_resource("Application")
        ec.register_connection(app1, node)

        app2 = ec.register_resource("Application")
        ec.register_connection(app2, node)

        ec.register_condition(app2, ResourceAction.START, app1, 
                ResourceState.STOPPED)

        ec.deploy()

        ec.wait_finished([app1, app2])
        
        rmapp1 = ec.get_resource(app1)
        rmapp2 = ec.get_resource(app2)

        self.assertTrue(rmapp2.start_time > rmapp1.stop_time)
        
        ec.shutdown()

    def ztest_set_with_condition(self):
        # TODO!!!
        pass


if __name__ == '__main__':
    unittest.main()

