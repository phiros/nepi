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
#         Maksym Gabielkov <maksym.gabielkovc@inria.fr>
#

## This is a maintenance script used to bootstrap the nodes from
## Nitos testbed (NITLab) before running a OMF experiment using
## Nitos nodes. This fixes the problem of Resource Controller 
## misbehaving by restarting it and it also loads the ath5k driver.

# Example of how to run this experiment (replace with your information):
#
# $ cd <path-to-nepi>
# python examples/linux/nitos_testbed_bootstrap.py -H <list-of-nitos-hosts> -u <nitos-username> -i <ssh-key> -g <nitos-gateway> -U <nitos-gateway-username>
#

from nepi.execution.ec import ExperimentController
from optparse import OptionParser, SUPPRESS_HELP
import os

usage = ("usage: %prog -H <list-of-nitos-hosts> -u <nitos-username> -i <ssh-key> -g <nitos-gateway> -U <nitos-gateway-username>")

parser = OptionParser(usage = usage)
parser.add_option("-H", "--hosts", dest="hosts", 
        help="Space separated list of hosts", type="str")
parser.add_option("-u", "--username", dest="username", 
        help="Username for the nitos hosts (usually root)", 
        type="str", default="root" )
parser.add_option("-g", "--gateway", dest="gateway", 
        help="Nitos gateway hostname", 
        type="str", default="nitlab.inf.uth.gr")
parser.add_option("-U", "--gateway-user", dest="gateway_username", 
        help="Nitos gateway username", 
        type="str", default="nitlab.inf.uth.gr")
parser.add_option("-i", "--ssh-key", dest="ssh_key", 
        help="Path to private SSH key to be used for connection", 
        type="str")
(options, args) = parser.parse_args()

hosts = options.hosts.split(" ")
username = options.username
gateway = options.gateway
gateway_username = options.gateway_username
ssh_key = options.ssh_key

apps = []

ec = ExperimentController(exp_id="ath5k")

for hostname in hosts:
    node = ec.register_resource("linux::Node")
    ec.set(node, "username", username)
    ec.set(node, "hostname", hostname)
    ec.set(node, "gateway", gateway)
    ec.set(node, "gatewayUser", gateway_username)
    ec.set(node, "cleanExperiment", True)

    app = ec.register_resource("linux::Application")
    ec.set(app, "command", "modprobe ath5k && ip a | grep wlan0 && service omf_rc restart")
    ec.register_connection(app, node)
   
    apps.append(app)

ec.deploy()
ec.wait_finished(apps)

for app in apps:
    print ec.trace(app, "stdout") 


