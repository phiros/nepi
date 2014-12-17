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

from optparse import OptionParser

usage = ("usage: %prog -H <hostanme> -u <username> -i <ssh-key>")

parser = OptionParser(usage = usage)
parser.add_option("-H", "--hostname", dest="hostname", 
        help="Remote host name or IP address", type="str")
parser.add_option("-u", "--username", dest="username", 
        help="Username to SSH to remote host", type="str")
parser.add_option("-i", "--ssh-key", dest="ssh_key", 
        help="Path to private SSH key to be used for connection", 
        type="str")
(options, args) = parser.parse_args()

hostname = options.hostname
username = options.username
identity = options.ssh_key

ec = ExperimentController(exp_id = "ns3-remote-p2p-ping")

# Simulation will run in a remote machine
node = ec.register_resource("linux::Node")
ec.set(node, "hostname", hostname)
ec.set(node, "username", username)
ec.set(node, "identity", identity)
ec.set(node, "cleanProcesses", True)
ec.set(node, "cleanExperiment", True)

# Add a simulation resource
simu = ec.register_resource("linux::ns3::Simulation")
ec.set(simu, "verbose", True)
ec.register_connection(simu, node)

## Add a ns-3 node with its protocol stack
nsnode1 = ec.register_resource("ns3::Node")
ec.register_connection(nsnode1, simu)

ipv4 = ec.register_resource("ns3::Ipv4L3Protocol")
ec.register_connection(nsnode1, ipv4)
arp = ec.register_resource("ns3::ArpL3Protocol")
ec.register_connection(nsnode1, arp)
icmp = ec.register_resource("ns3::Icmpv4L4Protocol")
ec.register_connection(nsnode1, icmp)

# Add a point to point net device to the node
dev1 = ec.register_resource("ns3::PointToPointNetDevice")
ec.set(dev1, "ip", "10.0.0.1")
ec.set(dev1, "prefix", "30")
ec.register_connection(nsnode1, dev1)
queue1 = ec.register_resource("ns3::DropTailQueue")
ec.register_connection(dev1, queue1)

## Add another ns-3 node with its protocol stack
nsnode2 = ec.register_resource("ns3::Node")
ec.register_connection(nsnode2, simu)

ipv4 = ec.register_resource("ns3::Ipv4L3Protocol")
ec.register_connection(nsnode2, ipv4)
arp = ec.register_resource("ns3::ArpL3Protocol")
ec.register_connection(nsnode2, arp)
icmp = ec.register_resource("ns3::Icmpv4L4Protocol")
ec.register_connection(nsnode2, icmp)

# Add a point to point net device to the node
dev2 = ec.register_resource("ns3::PointToPointNetDevice")
ec.set(dev2, "ip", "10.0.0.2")
ec.set(dev2, "prefix", "30")
ec.register_connection(nsnode2, dev2)
queue2 = ec.register_resource("ns3::DropTailQueue")
ec.register_connection(dev2, queue2)

# Add a point to point channel
chan = ec.register_resource("ns3::PointToPointChannel")
ec.set(chan, "Delay", "0s")
ec.register_connection(chan, dev1)
ec.register_connection(chan, dev2)

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

ec.shutdown()

print "PING OUTPUT", stdout
