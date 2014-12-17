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
from nepi.execution.resource import ResourceState, ResourceAction
from nepi.execution.trace import TraceAttr

from test_utils import skipIfNotAlive

import os
import time
import unittest

def add_ns3_node(ec, simu):
    node = ec.register_resource("ns3::Node")
    ec.register_connection(node, simu)

    ipv4 = ec.register_resource("ns3::Ipv4L3Protocol")
    ec.register_connection(node, ipv4)

    arp = ec.register_resource("ns3::ArpL3Protocol")
    ec.register_connection(node, arp)
    
    icmp = ec.register_resource("ns3::Icmpv4L4Protocol")
    ec.register_connection(node, icmp)

    udp = ec.register_resource("ns3::UdpL4Protocol")
    ec.register_connection(node, udp)

    return node

def add_fd_device(ec, node, ip, prefix):
    dev = ec.register_resource("ns3::FdNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)

    return dev

def add_tap_device(ec, node, ip, prefix):
    dev = ec.register_resource("linux::Tap")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)
    
    return dev

def add_point2point_device(ec, node, ip, prefix):
    dev = ec.register_resource("ns3::PointToPointNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)

    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

class LinuxNS3FdNetDeviceTest(unittest.TestCase):
    def setUp(self):
        self.fedora_host = "nepi2.pl.sophia.inria.fr"
        self.fedora_user = "inria_nepi"
        self.fedora_identity = "%s/.ssh/id_rsa_planetlab" % (os.environ['HOME'])

    @skipIfNotAlive
    def t_cross_ping(self, host, user = None, identity = None):
        ec = ExperimentController(exp_id = "test-linux-ns3-tap-fd")
        
        node = ec.register_resource("linux::Node")
        if host == "localhost":
            ec.set(node, "hostname", "localhost")
        else:
            ec.set(node, "hostname", host)
            ec.set(node, "username", user)
            ec.set(node, "identity", identity)
        
        ec.set(node, "cleanProcesses", True)
        ec.set(node, "cleanExperiment", True)

        simu = ec.register_resource("linux::ns3::Simulation")
        ec.set(simu, "simulatorImplementationType", "ns3::RealtimeSimulatorImpl")
        ec.set(simu, "checksumEnabled", True)
        ec.set(simu, "verbose", True)
        #ec.set(simu, "buildMode", "debug")
        #ec.set(simu, "nsLog", "FdNetDevice")
        ec.register_connection(simu, node)

        nsnode1 = add_ns3_node(ec, simu)
        dev1 = add_point2point_device(ec, nsnode1, "10.0.0.1", "30")

        nsnode2 = add_ns3_node(ec, simu)
        dev2 = add_point2point_device(ec, nsnode2, "10.0.0.2", "30")
        
        # Add routes on the NS3 side
        r1 = ec.register_resource("ns3::Route")
        ec.set(r1, "network", "10.0.1.0")
        ec.set(r1, "prefix", "30")
        ec.set(r1, "nexthop", "10.0.0.1")
        ec.register_connection(r1, nsnode2)

        # Create channel
        chan = ec.register_resource("ns3::PointToPointChannel")
        ec.set(chan, "Delay", "0s")
        ec.register_connection(chan, dev1)
        ec.register_connection(chan, dev2)

        fddev = add_fd_device(ec, nsnode1, "10.0.1.2", "30")
        ec.enable_trace(fddev, "pcap")
        ec.enable_trace(fddev, "promiscPcap")
        ec.enable_trace(fddev, "ascii")

        tap = add_tap_device(ec, node, "10.0.1.1", "30")

        crosslink = ec.register_resource("linux::ns3::TapFdLink")
        ec.register_connection(crosslink, tap)
        ec.register_connection(crosslink, fddev)

        # Add routes on the localhost side
        r2 = ec.register_resource("linux::Route")
        ec.set(r2, "network", "10.0.0.0")
        ec.set(r2, "prefix", "30")
        ec.set(r2, "nexthop", "10.0.1.2")
        ec.register_connection(r2, tap)

        app = ec.register_resource("linux::Application")
        ec.set(app, "command", "ping -c3 10.0.0.1")
        ec.register_connection(app, node)

        ec.register_condition(app, ResourceAction.START, simu, 
                ResourceState.STARTED, time="5s")

        ec.deploy()

        ec.wait_finished([app])

        stdout = ec.trace(app, "stdout")
        expected = "3 packets transmitted, 3 received, 0% packet loss"
        self.assertTrue(stdout.find(expected) > -1)

        ## Releasing to force ns3 to flush the traces
        ec.release()
        pcap = ec.trace(fddev, "pcap")

        self.assertTrue(len(pcap) > 4000)
        ec.shutdown()

    def ztest_cross_ping_fedora(self):
        self.t_cross_ping(self.fedora_host, self.fedora_user, self.fedora_identity)

    def test_cross_ping_local(self):
        self.t_cross_ping("localhost")


if __name__ == '__main__':
    unittest.main()

