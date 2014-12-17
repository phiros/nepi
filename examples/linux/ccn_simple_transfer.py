#
#    NEPI, a framework to manage network experiments
#    Copyright (C) 2014 INRIA
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
#

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/linux/ccn_simple_transfer.py -a <hostname1> -b <hostname2> -u <username> -i <ssh-key>

# CCN topology:
#
#                
#                 
#  content                  ccncat
#  Linux host               Linux host
#     0 ------- network -------- 1
#

from nepi.execution.ec import ExperimentController

from optparse import OptionParser
import os

usage = ("usage: %prog -a <hostname1> -b <hostname2> -u <username> -i <ssh-key>")

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
ec = ExperimentController(exp_id = "ccn_simple_transfer")

##### CONFIGURING NODE 1

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

## Register a CCN daemon in node 1
ccnd1 = ec.register_resource("linux::CCND")
# Set ccnd log level to 7
ec.set(ccnd1, "debug", 7)
ec.register_connection(ccnd1, node1)

## Register a repository in node 1
ccnr1 = ec.register_resource("linux::CCNR")
ec.register_connection(ccnr1, ccnd1)

## Push the file into the repository
local_path_to_content = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
            "..", "big_buck_bunny_240p_mpeg4_lq.ts")

content_name = "ccnx:/test/FILE"

# Add a content to the repository
co = ec.register_resource("linux::CCNContent")
ec.set(co, "contentName", content_name)
# NEPI will upload the specified file to the remote node and write it
# into the CCN repository
ec.set(co, "content", local_path_to_content)
ec.register_connection(co, ccnr1)

##### CONFIGURING NODE 2

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

## Register a CCN daemon in node 2
ccnd2 = ec.register_resource("linux::CCND")
# Set ccnd log level to 7
ec.set(ccnd2, "debug", 7)
ec.register_connection(ccnd2, node2)

## Retrieve the file stored in node 1 from node 2
ccncat = ec.register_resource("linux::CCNCat")
ec.set(ccncat, "contentName", content_name)
ec.register_connection(ccncat, ccnd2)

##### INTERCONNECTING CCN NODES ...

# Register a FIB entry from node 1 to node 2
entry1 = ec.register_resource("linux::FIBEntry")
ec.set(entry1, "host", hostname2)
ec.register_connection(entry1, ccnd1)

# Register a FIB entry from node 2 to node 1
entry2 = ec.register_resource("linux::FIBEntry")
ec.set(entry2, "host", hostname1)
ec.register_connection(entry2, ccnd2)

##### STARTING THE EXPERIMENT

## Deploy all resources
ec.deploy()

# Wait until the ccncat is finished
ec.wait_finished([ccncat])

stdout = ec.trace(ccncat, "stdout")
f = open("video.ts", "w")
f.write(stdout)
f.close()

ec.shutdown()

print "Transfered FILE stored localy at video.ts"
