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

ec = ExperimentController(exp_id = "ns3-local-wifi-ping")

# Simulation will executed in the local machine
node = ec.register_resource("linux::Node")
ec.set(node, "hostname", "localhost")

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

# Adding constant mobility to the ns-3 node
mobility1 = ec.register_resource("ns3::ConstantPositionMobilityModel") 
position1 = "%d:%d:%d" % (0, 0, 0)
ec.set(mobility1, "Position", position1)
ec.register_connection(nsnode1, mobility1)

# Add a wifi access point net device to the node
dev1 = ec.register_resource("ns3::WifiNetDevice")
ec.set(dev1, "ip", "10.0.0.1")
ec.set(dev1, "prefix", "30")
ec.register_connection(nsnode1, dev1)

phy1 = ec.register_resource("ns3::YansWifiPhy")
ec.set(phy1, "Standard", "WIFI_PHY_STANDARD_80211a")
ec.register_connection(dev1, phy1)

error1 = ec.register_resource("ns3::NistErrorRateModel")
ec.register_connection(phy1, error1)

manager1 = ec.register_resource("ns3::ArfWifiManager")
ec.register_connection(dev1, manager1)

# Mark the node as a wireless access point
mac1 = ec.register_resource("ns3::ApWifiMac")
ec.set(mac1, "Standard", "WIFI_PHY_STANDARD_80211a")
ec.register_connection(dev1, mac1)

## Add another ns-3 node with its protocol stack
nsnode2 = ec.register_resource("ns3::Node")
ec.register_connection(nsnode2, simu)

ipv4 = ec.register_resource("ns3::Ipv4L3Protocol")
ec.register_connection(nsnode2, ipv4)
arp = ec.register_resource("ns3::ArpL3Protocol")
ec.register_connection(nsnode2, arp)
icmp = ec.register_resource("ns3::Icmpv4L4Protocol")
ec.register_connection(nsnode2, icmp)

# Adding constant mobility to the ns-3 node
mobility2 = ec.register_resource("ns3::ConstantPositionMobilityModel") 
position2 = "%d:%d:%d" % (50, 50, 0)
ec.set(mobility2, "Position", position2)
ec.register_connection(nsnode2, mobility2)

# Add a wifi station net device to the node
dev2 = ec.register_resource("ns3::WifiNetDevice")
ec.set(dev2, "ip", "10.0.0.2")
ec.set(dev2, "prefix", "30")
ec.register_connection(nsnode2, dev2)

phy2 = ec.register_resource("ns3::YansWifiPhy")
ec.set(phy2, "Standard", "WIFI_PHY_STANDARD_80211a")
ec.register_connection(dev2, phy2)

error2 = ec.register_resource("ns3::NistErrorRateModel")
ec.register_connection(phy2, error2)

manager2 = ec.register_resource("ns3::ArfWifiManager")
ec.register_connection(dev2, manager2)

# Mark the node as a wireless station
mac2 = ec.register_resource("ns3::StaWifiMac")
ec.set(mac2, "Standard", "WIFI_PHY_STANDARD_80211a")
ec.register_connection(dev2, mac2)

# Add a wifi channel
chan = ec.register_resource("ns3::YansWifiChannel")
delay = ec.register_resource("ns3::ConstantSpeedPropagationDelayModel")
ec.register_connection(chan, delay)
loss = ec.register_resource("ns3::LogDistancePropagationLossModel")
ec.register_connection(chan, loss)
ec.register_connection(chan, phy1)
ec.register_connection(chan, phy2)

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
