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

class LinuxNS3FdNetDeviceTest(unittest.TestCase):
    def setUp(self):
        self.fedora_host = "nepi2.pl.sophia.inria.fr"
        self.fedora_user = "inria_nepi"
        self.fedora_identity = "%s/.ssh/id_rsa_planetlab" % (os.environ['HOME'])

    @skipIfNotAlive
    def t_dummy(self, host, user = None, identity = None):
        ec = ExperimentController(exp_id = "test-ns3-fd-dummy")
        
        node = ec.register_resource("linux::Node")
        if host == "localhost":
            ec.set(node, "hostname", "localhost")
        else:
            ec.set(node, "hostname", host)
            ec.set(node, "username", user)
            ec.set(node, "identity", identity)
        
        ec.set(node, "cleanProcesses", True)
        #ec.set(node, "cleanExperiment", True)

        simu = ec.register_resource("linux::ns3::Simulation")
        ec.set(simu, "simulatorImplementationType", "ns3::RealtimeSimulatorImpl")
        ec.set(simu, "checksumEnabled", True)
        ec.set(simu, "verbose", True)
        ec.register_connection(simu, node)

        nsnode1 = add_ns3_node(ec, simu)
        dev1 = add_fd_device(ec, nsnode1, "10.0.0.1", "30")

        nsnode2 = add_ns3_node(ec, simu)
        dev2 = add_fd_device(ec, nsnode2, "10.0.0.2", "30")
        
        channel = ec.register_resource("ns3::PipeChannel")
        ec.register_connection(channel, dev1)
        ec.register_connection(channel, dev2)

        ### create pinger
        ping = ec.register_resource("ns3::V4Ping")
        ec.set (ping, "Remote", "10.0.0.2")
        ec.set (ping, "Interval", "1s")
        ec.set (ping, "Verbose", True)
        ec.set (ping, "StartTime", "0s")
        ec.set (ping, "StopTime", "20s")
        ec.register_connection(ping, nsnode1)

        ec.deploy()

        ec.wait_finished([ping])

        stdout = ec.trace(simu, "stdout") 

        print stdout

        expected = "20 packets transmitted, 20 received, 0% packet loss"
        self.assertTrue(stdout.find(expected) > -1)

        ec.shutdown()

    def ztest_dummy_fedora(self):
        self.t_dummy(self.fedora_host, self.fedora_user, self.fedora_identity)

    def test_dummy_local(self):
        self.t_dummy("localhost")


if __name__ == '__main__':
    unittest.main()

