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

import os

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

def add_device(ec, node, ip,  prefix):
    dev = ec.register_resource("ns3::PointToPointNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)

    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

ec = ExperimentController(exp_id = "dce-custom-ccn")

node = ec.register_resource("linux::Node")
ec.set(node, "hostname", "localhost")
ec.set(node, "cleanProcesses", True)

simu = ec.register_resource("linux::ns3::Simulation")
ec.set(simu, "verbose", True)
ec.register_connection(simu, node)

nsnode1 = add_ns3_node(ec, simu)
dev1 = add_device(ec, nsnode1, "10.0.0.1", "30")
ec.set(dev1, "DataRate", "5Mbps")

nsnode2 = add_ns3_node(ec, simu)
dev2 = add_device(ec, nsnode2, "10.0.0.2", "30")
ec.set(dev2, "DataRate", "5Mbps")

# Create channel
chan = ec.register_resource("ns3::PointToPointChannel")
ec.set(chan, "Delay", "2ms")

ec.register_connection(chan, dev1)
ec.register_connection(chan, dev2)

### create applications

# Add a LinuxCCNDceApplication to ns-3 node 1 to install custom ccnx sources
# and run a CCNx daemon
ccnd1 = ec.register_resource("linux::ns3::dce::CCNApplication")
# NOTE THAT INSTALLATION MIGHT FAIL IF openjdk-6-jdk is not installed
ec.set(ccnd1, "depends", "libpcap0.8-dev openjdk-6-jdk ant1.8 autoconf "
    "libssl-dev libexpat-dev libpcap-dev libecryptfs0 libxml2-utils auto"
    "make gawk gcc g++ git-core pkg-config libpcre3-dev openjdk-6-jre-lib")
ec.set (ccnd1, "sources", "http://www.ccnx.org/releases/ccnx-0.7.2.tar.gz")
ec.set (ccnd1, "build", "tar zxf ${SRC}/ccnx-0.7.2.tar.gz && "
        "cd ccnx-0.7.2 && "
        " INSTALL_BASE=${BIN_DCE}/.. ./configure && "
        " make MORE_LDLIBS='-pie -rdynamic' && "
        " make install && "
        " cp ${BIN_DCE}/../bin/ccn* ${BIN_DCE} && "
        " cd -")
ec.set (ccnd1, "binary", "ccnd")
ec.set (ccnd1, "stackSize", 1<<20)
ec.set (ccnd1, "environment", "CCND_CAP=50000; CCND_DEBUG=7")
ec.set (ccnd1, "StartTime", "1s")
ec.set (ccnd1, "StopTime", "20s")
ec.register_connection(ccnd1, nsnode1)

# Add a CCN repository to ns-3 node1 manually configuring all
# parameters
repofile = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 
    "..", "..", "test", "resources", "linux", 
    "ns3", "ccn", "repoFile1")

ccnr = ec.register_resource("linux::ns3::dce::CCNApplication")
ec.set (ccnr, "binary", "ccnr")
ec.set (ccnr, "environment", "CCNR_DIRECTORY=/REPO/")
ec.set (ccnr, "files", "%s=/REPO/repoFile1" % repofile) 
ec.set (ccnr, "stackSize", 1<<20)
ec.set (ccnr, "StartTime", "2s")
ec.set (ccnr, "StopTime", "120s")
ec.register_connection(ccnr, nsnode1)

# Add a LinuxCCNDceApplication to ns-3 node 1 to run a CCN
# daemon. Note that the CCNx sources and build instructions 
# do not need to be specified again (NEPI will take the 
# instructions from the first definition).
ccnd2 = ec.register_resource("linux::ns3::dce::CCNApplication")
ec.set (ccnd2, "binary", "ccnd")
ec.set (ccnd2, "stackSize", 1<<20)
ec.set (ccnd2, "environment", "CCND_CAP=50000; CCND_DEBUG=7")
ec.set (ccnd2, "StartTime", "1s")
ec.set (ccnd2, "StopTime", "120s")
ec.register_connection(ccnd2, nsnode2)

# Add DCE application to configure peer CCN faces between
# nodes
ccndc1 = ec.register_resource("linux::ns3::dce::CCNApplication")
ec.set (ccndc1, "binary", "ccndc")
ec.set (ccndc1, "arguments", "-v;add;ccnx:/;udp;10.0.0.2")
ec.set (ccndc1, "stackSize", 1<<20)
ec.set (ccndc1, "StartTime", "2s")
ec.set (ccndc1, "StopTime", "120s")
ec.register_connection(ccndc1, nsnode1)

ccndc2 = ec.register_resource("linux::ns3::dce::CCNApplication")
ec.set (ccndc2, "binary", "ccndc")
ec.set (ccndc2, "arguments", "-v;add;ccnx:/;udp;10.0.0.1")
ec.set (ccndc2, "stackSize", 1<<20)
ec.set (ccndc2, "StartTime", "2s")
ec.set (ccndc2, "StopTime", "120s")
ec.register_connection(ccndc2, nsnode2)

# Add a DCE application to perform a ccncat and retrieve content
ccncat = ec.register_resource("linux::ns3::dce::CCNApplication")
ec.set (ccncat, "binary", "ccncat")
ec.set (ccncat, "arguments", "ccnx:/test/bunny.ts")
ec.set (ccncat, "stdinFile", "")
ec.set (ccncat, "stackSize", 1<<20)
ec.set (ccncat, "StartTime", "4s")
ec.set (ccncat, "StopTime", "120s")
ec.register_connection(ccncat, nsnode2)

ec.deploy()

ec.wait_finished([ccncat])

stdout = ec.trace(ccncat, "stdout")
# convert from bytes to MB
print "%0.2f MBytes received" % (len(stdout) / 1024.0 / 1024.0 )

ec.shutdown()

