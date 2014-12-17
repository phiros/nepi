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
# python examples/planetlab/select_nodes.py -s <pl-slice> -u <pl-user> -p <pl-password> -k <pl-ssh-key> -c <country> -o <operating-system> -n <node-count> 


from nepi.execution.ec import ExperimentController

from optparse import OptionParser
import os

usage = ("usage: %prog -s <pl-slice> -u <pl-user> -p <pl-password> "
    "-k <pl-ssh-key> -c <country> -o <operating-system> -n <node-count> ")

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
parser.add_option("-c", "--country", dest="country",
        help="Country for the PL hosts",
        type="str")
parser.add_option("-o", "--os", dest="os",
        help="Operating system for the PL hosts",
        type="str")
parser.add_option("-n", "--node-count", dest="node_count",
        help="Number of PL hosts to provision",
        default = 2,
        type="int")

(options, args) = parser.parse_args()

pl_slice = options.pl_slice
pl_ssh_key = options.pl_ssh_key
pl_user = options.pl_user
pl_password = options.pl_password
country = options.country
os = options.os
node_count = options.node_count

def add_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, country, os):
    node = ec.register_resource("planetlab::Node")
    ec.set(node, "username", pl_slice)
    ec.set(node, "identity", pl_ssh_key)
    ec.set(node, "pluser", pl_user)
    ec.set(node, "plpassword", pl_password)

    if country:
        ec.set(node, "country", country)
    if os:
        ec.set(node, "operatingSystem", os)

    ec.set(node, "cleanExperiment", True)
    ec.set(node, "cleanProcesses", True)

    return node

## Create the experiment controller
ec = ExperimentController(exp_id="host_select")

nodes = []

for i in xrange(node_count):
    node = add_node(ec, pl_slice, pl_ssh_key, pl_user, pl_password, country, os)
    nodes.append(node)

ec.deploy()

ec.wait_deployed(nodes)

print "SELECTED HOSTS"

for node in nodes:
    print ec.get(node, "hostname")

ec.shutdown()


