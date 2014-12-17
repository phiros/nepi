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
# Author: Lucia Guevgeozian <lucia.guevgeozian_odizzio@inria.fr>
#         Alina Quereilhac <alina.quereilhac@inria.fr>
#
#
# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/linux/netcat_file_transfer.py -a <hostname1> -b <hostname2> -u <username> -i <ssh-key>

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState

from optparse import OptionParser, SUPPRESS_HELP
import os

usage = ("usage: %prog -a <hostanme1> -b <hostname2> -u <username> -i <ssh-key>")

parser = OptionParser(usage = usage)
parser.add_option("-a", "--hostname1", dest="hostname1", 
        help="Remote host 1", type="str")
parser.add_option("-b", "--hostname2", dest="hostname2", 
        help="Remote host 2", type="str")
parser.add_option("-u", "--username", dest="username", 
        help="Username to SSH to remote host", type="str")
parser.add_option("-i", "--ssh-key", dest="ssh_key", 
        help="Path to private SSH key to be used for connection", 
        type="str")
(options, args) = parser.parse_args()

hostname1 = options.hostname1
hostname2 = options.hostname2
username = options.username
ssh_key = options.ssh_key

## Create the experiment controller
ec = ExperimentController(exp_id = "nc_file_transfer")

## Register node 1
node1 = ec.register_resource("linux::Node")
# Set the hostname of the first node to use for the experiment
ec.set(node1, "hostname", hostname1)
# username should be your SSH user 
ec.set(node1, "username", username)
# Absolute path to the SSH private key
ec.set(node1, "identity", ssh_key)
# Clean all files, results, etc, from previous experiments wit the same exp_id
ec.set(node1, "cleanExperiment", True)
# Kill all running processes in the node before running the experiment
ec.set(node1, "cleanProcesses", True)

## Register node 2 
node2 = ec.register_resource("linux::Node")
# Set the hostname of the first node to use for the experiment
ec.set(node2, "hostname", hostname2)
# username should be your SSH user 
ec.set(node2, "username", username)
# Absolute path to the SSH private key
ec.set(node2, "identity", ssh_key)
# Clean all files, results, etc, from previous experiments wit the same exp_id
ec.set(node2, "cleanExperiment", True)
# Kill all running processes in the node before running the experiment
ec.set(node2, "cleanProcesses", True)

# Register server
video = "big_buck_bunny_240p_mpeg4_lq.ts"
local_path_to_video = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
            "..", video)

command = "cat ${SHARE}/%s | pv -fbt 2> bw.txt | nc %s 1234" % ( 
        video, hostname2 )

server = ec.register_resource("linux::Application")
ec.set(server, "depends", "pv nc tcpdump")
ec.set(server, "files", local_path_to_video)
ec.set(server, "command", command)
ec.register_connection(server, node1)

# Register client
# Note: is important to add the -d option in nc command to not attempt to read from the 
# stdin
# if not nc in the client side close the socket suddently if runned in background
command =  "nc -dl 1234 > %s" % video

client = ec.register_resource("linux::Application")
ec.set(client, "depends", "nc")
ec.set(client, "command", command)
ec.register_connection(client, node2)

# Register a tcpdump in the server node to monitor the file transfer 
command = "tcpdump -ni eth0 -w file_transfer.pcap -s0 port 1234 2>&1"

capture = ec.register_resource("linux::Application")
ec.set(capture, "depends", "tcpdump")
ec.set(capture, "command", command)
ec.set(capture, "sudo", True)
ec.register_connection(capture, node1)

# Register conditions 1. nodes ; 2. start tcpdump capture ; 3. client listen port 1234 ;
# 4. server start sending video
ec.register_condition(server, ResourceAction.START, client, ResourceState.STARTED) 
ec.register_condition(client, ResourceAction.START, capture, ResourceState.STARTED)

# Deploy
ec.deploy()

# Wait until the applications are finish to retrive the traces
ec.wait_finished([server, client])

# Retrieve traces from nc and tcpdump
bw = ec.trace(server, "bw.txt")
pcap = ec.trace(capture, "file_transfer.pcap")

# Choose a directory to store the traces, example f = open("/home/<user>/bw.txt", "w")
f = open("bw.txt", "w")
f.write(bw)
f.close()
f = open("video_transfer.pcap", "w")
f.write(pcap)
f.close()

ec.shutdown()

print "Total bytes transfered saved to bw.txt..."

