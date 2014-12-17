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

# NOTE: This experiment example uses the generic LinuxApplication
#       ResourceManager to do the CCN set up in the hosts.
#       Alternatively, CCN specific ResourceManagers can be used
#       (i.e. LinuxCCND, LinuxCCNR, etc...), and those require less 
#       manual configuration.
#
#

# CCN topology:
#
#                
#                 
#  content                ccncat
#  Linux host               Linux host
#  0 ------- Internet ------ 0
#           

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/linux/ccn_advanced_transfer.py -a <hostname1> -b <hostname2> -u <username> -i <ssh-key>

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState

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

def add_node(ec, host, user, ssh_key = None):
    node = ec.register_resource("linux::Node")
    ec.set(node, "hostname", host)
    ec.set(node, "username", user)
    ec.set(node, "identity", ssh_key)
    ec.set(node, "cleanHome", True)
    ec.set(node, "cleanProcesses", True)
    return node

def add_ccnd(ec, peers):
    # Dependencies for Fedora
    depends = ( " autoconf openssl-devel  expat-devel libpcap-devel "
                " ecryptfs-utils-devel libxml2-devel automake gawk " 
                " gcc gcc-c++ git pcre-devel make ")

    # UBUNTU / DEBIAN
    # depends = ( " autoconf libssl-dev libexpat-dev libpcap-dev "
    #            " libecryptfs0 libxml2-utils automake gawk gcc g++ "
    #            " git-core pkg-config libpcre3-dev make ")

    sources = "http://www.ccnx.org/releases/ccnx-0.8.2.tar.gz"

    build = (
        # Evaluate if ccnx binaries are already installed
        " ( "
            "  test -f ${BIN}/ccnx-0.8.2/bin/ccnd"
        " ) || ( "
        # If not, untar and build
            " ( "
            " mkdir -p ${SRC}/ccnx-0.8.2 && "
                " tar xf ${SRC}/ccnx-0.8.2.tar.gz --strip-components=1 -C ${SRC}/ccnx-0.8.2 "
             " ) && "
                "cd ${SRC}/ccnx-0.8.2 && "
                # Just execute and silence warnings...
                "( ./configure && make ) "
         " )") 

    install = (
        # Evaluate if ccnx binaries are already installed
        " ( "
            "  test -f ${BIN}/ccnx-0.8.2/bin/ccnd"
        " ) || ( "
            "  mkdir -p ${BIN}/ccnx-0.8.2/bin && "
            "  cp -r ${SRC}/ccnx-0.8.2/bin ${BIN}/ccnx-0.8.2"
        " )"
    )

    env = "PATH=$PATH:${BIN}/ccnx-0.8.2/bin"

    # BASH command -> ' ccndstart ; ccndc add ccnx:/ udp  host ;  ccnr '
    command = "ccndstart && "
    peers = map(lambda peer: "ccndc add ccnx:/ udp  %s" % peer, peers)
    command += " ; ".join(peers) + " && "
    command += " ccnr & "

    app = ec.register_resource("linux::Application")
    ec.set(app, "depends", depends)
    ec.set(app, "sources", sources)
    ec.set(app, "install", install)
    ec.set(app, "build", build)
    ec.set(app, "env", env)
    ec.set(app, "command", command)

    return app

def add_publish(ec, movie, content_name):
    env = "PATH=$PATH:${BIN}/ccnx-0.8.2/bin"
    command = "ccnseqwriter -r %s" % content_name

    app = ec.register_resource("linux::Application")
    ec.set(app, "stdin", movie)
    ec.set(app, "env", env)
    ec.set(app, "command", command)

    return app

def add_ccncat(ec, content_name):
    env = "PATH=$PATH:${BIN}/ccnx-0.8.2/bin"
    command = "ccncat %s" % content_name

    app = ec.register_resource("linux::Application")
    ec.set(app, "env", env)
    ec.set(app, "command", command)

    return app

## Create the experiment controller
ec = ExperimentController(exp_id = "ccn_advanced_transfer")

# Register first PlanetLab host
node1 = add_node(ec, hostname1, username, ssh_key)

# Register CCN setup for host
peers = [hostname2]
ccnd1 = add_ccnd(ec, peers)
ec.register_connection(ccnd1, node1)

# Register content producer application (ccnseqwriter)
## Push the file into the repository
local_path_to_content = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
            "..", "big_buck_bunny_240p_mpeg4_lq.ts")

content_name = "ccnx:/test/FILE"

pub = add_publish(ec, local_path_to_content, content_name)
ec.register_connection(pub, node1)

# The movie can only be published after ccnd is running
ec.register_condition(pub, ResourceAction.START, 
        ccnd1, ResourceState.STARTED)

# Register Linux host
node2 = add_node(ec, hostname2, username, ssh_key)

# Register CCN setup for Linux host
peers = [hostname1]
ccnd2 = add_ccnd(ec, peers)
ec.register_connection(ccnd2, node2)
 
# Register consumer application (ccncat)
ccncat = add_ccncat(ec, content_name)
ec.register_connection(ccncat, node2)

# The file can only be retrieved after ccnd is running
ec.register_condition(ccncat, ResourceAction.START, 
        ccnd2, ResourceState.STARTED)

# And also, the file can only be retrieved after it was published
ec.register_condition(ccncat, ResourceAction.START, 
        pub, ResourceState.STARTED)

# Deploy all ResourceManagers
ec.deploy()

# Wait until the applications are finished
apps = [ccncat]
ec.wait_finished(apps)

stdout = ec.trace(ccncat, "stdout")
f = open("video.ts", "w")
f.write(stdout)
f.close()

# Shutdown the experiment controller
ec.shutdown()

print "Transfered FILE stored localy at video.ts"

