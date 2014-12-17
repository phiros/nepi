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

    tcp = ec.register_resource("ns3::TcpL4Protocol")
    ec.register_connection(node, tcp)

    return node

def add_point2point_device(ec, node, ip,  prefix):
    dev = ec.register_resource("ns3::PointToPointNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)

    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

class LinuxNS3PingDceApplicationTest(unittest.TestCase):
    def setUp(self):
        self.fedora_host = "nepi2.pl.sophia.inria.fr"
        self.fedora_user = "inria_nepi"
        self.fedora_identity = "%s/.ssh/id_rsa_planetlab" % (os.environ['HOME'])

    @skipIfNotAlive
    def t_dce_ping(self, host, user = None, identity = None):
        ec = ExperimentController(exp_id = "test-dce-ping-app")

        node = ec.register_resource("linux::Node")
        if host == "localhost":
            ec.set(node, "hostname", host)
        else:
            ec.set(node, "hostname", host)
            ec.set(node, "username", user)
            ec.set(node, "identity", identity)
        
        ec.set(node, "cleanProcesses", True)
        #ec.set(node, "cleanHome", True)

        simu = ec.register_resource("linux::ns3::Simulation")
        ec.set(simu, "verbose", True)
        ec.set(simu, "buildMode", "debug")
        ec.set(simu, "nsLog", "DceApplication")
        ec.register_connection(simu, node)

        nsnode1 = add_ns3_node(ec, simu)
        p2p1 = add_point2point_device(ec, nsnode1, "10.0.0.1", "30")
        ec.set(p2p1, "DataRate", "5Mbps")

        nsnode2 = add_ns3_node(ec, simu)
        p2p2 = add_point2point_device(ec, nsnode2, "10.0.0.2", "30")
        ec.set(p2p2, "DataRate", "5Mbps")

        # Create channel
        chan = ec.register_resource("ns3::PointToPointChannel")
        ec.set(chan, "Delay", "2ms")

        ec.register_connection(chan, p2p1)
        ec.register_connection(chan, p2p2)

        ### create applications
        ping = ec.register_resource("linux::ns3::dce::Ping")
        ec.set (ping, "stackSize", 1<<20)
        ec.set (ping, "target", "10.0.0.2")
        ec.set (ping, "count", "10")
        ec.set (ping, "packetSize", "1000")
        ec.set (ping, "StartTime", "1s")
        ec.set (ping, "StopTime", "20s")
        ec.register_connection(ping, nsnode1)

        ec.deploy()

        ec.wait_finished([ping])

        expected = "ping -c 10 -s 1000 10.0.0.2"
        cmdline = ec.trace(ping, "cmdline")
        self.assertTrue(cmdline.find(expected) > -1, cmdline)
        
        expected = "Start Time: NS3 Time:          1s ("
        status = ec.trace(ping, "status")
        self.assertTrue(status.find(expected) > -1, status)

        expected = "10 packets transmitted, 10 received, 0% packet loss, time 9002ms"
        stdout = ec.trace(ping, "stdout")
        self.assertTrue(stdout.find(expected) > -1, stdout)

        stderr = ec.trace(simu, "stderr")
        expected = "DceApplication:StartApplication"
        self.assertTrue(stderr.find(expected) > -1, stderr)

        ec.shutdown()

    def test_dce_ping_fedora(self):
        self.t_dce_ping(self.fedora_host, self.fedora_user, self.fedora_identity)

    def test_dce_ping_local(self):
        self.t_dce_ping("localhost")

if __name__ == '__main__':
    unittest.main()
