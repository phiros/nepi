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

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/linux/ping.py -a <hostname> -u <username> -i <ssh-key>


from nepi.execution.ec import ExperimentController 

from optparse import OptionParser, SUPPRESS_HELP
import os

usage = ("usage: %prog -a <hostanme> -u <username> -i <ssh-key>")

parser = OptionParser(usage = usage)
parser.add_option("-a", "--hostname", dest="hostname", 
        help="Remote host", type="str")
parser.add_option("-u", "--username", dest="username", 
        help="Username to SSH to remote host", type="str")
parser.add_option("-i", "--ssh-key", dest="ssh_key", 
        help="Path to private SSH key to be used for connection", 
        type="str")
(options, args) = parser.parse_args()

hostname = options.hostname
username = options.username
ssh_key = options.ssh_key

ec = ExperimentController(exp_id = "ping-exp")
        
node = ec.register_resource("linux::Node")
ec.set(node, "hostname", hostname)
ec.set(node, "username", username)
ec.set(node, "identity", ssh_key)
ec.set(node, "cleanExperiment", True)
ec.set(node, "cleanProcesses", True)

app = ec.register_resource("linux::Application")
ec.set(app, "command", "ping -c3 nepi.inria.fr")
ec.register_connection(app, node)

ec.deploy()

ec.wait_finished(app)

print ec.trace(app, "stdout")

ec.shutdown()

