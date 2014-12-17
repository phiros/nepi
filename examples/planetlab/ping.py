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

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/planetlab/ping.py -s <pl-slice> -u <pl-user> -p <pl-password> -k <pl-ssh-key>  


from nepi.execution.ec import ExperimentController

from optparse import OptionParser
import os

usage = ("usage: %prog -s <pl-slice> -u <pl-user> -p <pl-password> "
     "-k <pl-ssh-key>")

parser = OptionParser(usage = usage)
parser.add_option("-s", "--pl-slice", dest="pl_slice",
        help="PlanetLab slicename", type="str")
parser.add_option("-u", "--pl-user", dest="pl_user",
        help="PlanetLab web username", type="str")
parser.add_option("-p", "--pl-password", dest="pl_password",
        help="PlanetLab web password", type="str")
parser.add_option("-k", "--pl-ssh-key", dest="pl_ssh_key",
        help="Path to private SSH key associated with the PL account",
        type="str")

(options, args) = parser.parse_args()

pl_slice = options.pl_slice
pl_ssh_key = options.pl_ssh_key
pl_user = options.pl_user
pl_password = options.pl_password

## Create the experiment controller
ec = ExperimentController(exp_id = "pl_ping")

# Register a Planetlab Node with no restrictions, it can be any node
node = ec.register_resource("planetlab::Node")

# The username in this case is the slice name, the one to use for login in 
# via ssh into PlanetLab nodes. Replace with your own slice name.
ec.set(node, "username", pl_slice)
ec.set(node, "identity", pl_ssh_key)

# The pluser and plpassword are the ones used to login in the PlanetLab web 
# site. Replace with your own user and password account information.
ec.set(node, "pluser", pl_user)
ec.set(node, "plpassword", pl_password)

# Remove previous results
ec.set(node, "cleanExperiment", True)
ec.set(node, "cleanProcesses", True)

# Define a ping application
app = ec.register_resource("linux::Application")
ec.set(app, "command", "ping -c3 nepi.inria.fr")

# Connect the application to the node
ec.register_connection(node, app)
    
# Deploy the experiment:
ec.deploy()

# Wait until the application is finish to retrive the trace:
ec.wait_finished(app)

trace = ec.trace(app, "stdout")

print "PING outout ", trace

# Do the experiment controller shutdown
ec.shutdown()

# END
