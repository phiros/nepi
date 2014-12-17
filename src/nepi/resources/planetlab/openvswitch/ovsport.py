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
# Authors: Alina Quereilhac <alina.quereilhac@inria.fr>
#         Alexandros Kouvakas <alexandros.kouvakas@inria.fr>
#         Julien Tribino <julien.tribino@inria.fr>

from nepi.execution.attribute import Attribute, Flags, Types
from nepi.execution.resource import ResourceManager, clsinit_copy, \
        ResourceState
from nepi.resources.planetlab.openvswitch.ovs import OVSSwitch        
from nepi.resources.planetlab.node import PlanetlabNode        
from nepi.resources.linux.application import LinuxApplication

import os

@clsinit_copy                 
class OVSPort(LinuxApplication):
    """
    .. class:: Class Args :
      
        :param ec: The Experiment controller
        :type ec: ExperimentController
        :param guid: guid of the RM
        :type guid: int

    """
    
    _rtype = "planetlab::OVSPort"
    _help = "Runs an OpenVSwitch on a PlanetLab host"
    _backend = "planetlab"

    _authorized_connections = ["planetlab::OVSSwitch", "linux::UdpTunnel", "linux::Tunnel"]      

    @classmethod
    def _register_attributes(cls):
        """ Register the attributes of OVSPort RM 

        """
        port_name = Attribute("port_name", "Name of the port",
            flags = Flags.Design)			
        ip = Attribute("ip", "IP of the endpoint. This is the attribute " 
                                "you should use to establish a tunnel or a remote "
                                "connection between endpoint",
            flags = Flags.Design)
        network = Attribute("network", "Network used by the port",
            flags = Flags.Design)	

        cls._register_attribute(port_name)
        cls._register_attribute(ip)
        cls._register_attribute(network)

    def __init__(self, ec, guid):
        """
        :param ec: The Experiment controller
        :type ec: ExperimentController
        :param guid: guid of the RM
        :type guid: int
    
        """
        super(OVSPort, self).__init__(ec, guid)


        self._port_number = None
        # in case of connection by tunnel	 
        self._remote_ip = None    

    def log_message(self, msg):
        return " guid %d - OVSPort - %s " % (self.guid, msg)

    @property
    def node(self):
        """ Node that run the switch and the ports
        """
        rm_list = self.get_connected(OVSSwitch.get_rtype())
        if rm_list:
            for elt in rm_list:
                node = elt.get_connected(PlanetlabNode.get_rtype())
                if node: return node[0]
        return node[0]

    @property
    def ovsswitch(self):
        """ Switch where the port is created
        """
        ovsswitch = self.get_connected(OVSSwitch.get_rtype())
        if ovsswitch: return ovsswitch[0]
        return None
        
    @property
    def remote_ip(self):
        return self._remote_ip

    @property
    def port_number(self):
        return self._port_number

    def valid_connection(self, guid):
        """ Check if the connection is available.

        :param guid: Guid of the current RM
        :type guid: int
        :rtype:  Boolean

        """
        rm = self.ec.get_resource(guid)
        if rm.get_rtype() in self._authorized_connections:
            msg = "Connection between %s %s and %s %s accepted" % (self.get_rtype(), self._guid, rm.get_rtype(), guid)
            self.debug(msg)
            return True
        msg = "Connection between %s %s and %s %s refused" % (self.get_rtype(), self._guid, rm.get_rtype(), guid)
        self.debug(msg)

    def create_port(self):
        """ Create the desired port
        """
        msg = "Creating the port %s" % self.get('port_name')
        self.debug(msg)

        if not self.get('port_name'):
            msg = "The port name is not assigned"
            self.error(msg)
            raise AttributeError, msg

        if not self.ovsswitch:
            msg = "The OVSwitch RM is not running"
            self.error(msg)
            raise AttributeError, msg

        cmd = "sliver-ovs create-port %s %s" % (self.ovsswitch.get('bridge_name'),
                                                self.get('port_name'))   
        self.node.run(cmd, self.ovsswitch.ovs_checks, 
                stderr = "stdout-%s" % self.get('port_name'), 
                stdout = "stderr-%s" % self.get('port_name'),
                sudo = True)

        self.info("Created the port %s on switch %s" % (self.get('port_name'),
                                             self.ovsswitch.get('bridge_name')))     
	    
    def initiate_udp_connection(self, remote_endpoint, connection_app_home, 
            connection_run_home, cipher, cipher_key, bwlimit, txqueuelen):
        """ Get the local_endpoint of the port
        """

        self._remote_ip = remote_endpoint.node.get("ip")

        msg = "Discovering the number of the port %s" % self.get('port_name')
        self.info(msg)

        command = "sliver-ovs get-local-endpoint %s" % self.get('port_name')
        out = err = ""
        (out, err), proc = self.node.run_and_wait(command, 
                self.ovsswitch.ovs_checks,
                shfile = "port_number-%s.sh" % self.get('port_name'),
                pidfile = "port_number_pidfile-%s" % self.get('port_name'),
                ecodefile = "port_number_exitcode-%s" % self.get('port_name'), 
                sudo = True, 
                stdout = "stdout-%s" % self.get('port_name'),    
                stderr = "stderr-%s" % self.get('port_name'))

        if err != "":
            msg = "Error retrieving the local endpoint of the port"
            self.error(msg)
            raise AttributeError, msg

        if out:
            self._port_number = int(out)

        self.info("The number of the %s is %s" % (self.get('port_name'), 
           self.port_number))

        if remote_endpoint.is_rm_instance("planetlab::Tap"):
            self._vroute = self.ec.register_resource("planetlab::Vroute")
            self.ec.set(self._vroute, "action", "add")
            self.ec.set(self._vroute, "network", self.get("network"))

            print "Vroute Guid :" + str(self._vroute)

            self.ec.register_connection(self._vroute, remote_endpoint.guid)
            self.ec.deploy(guids=[self._vroute], group = self.deployment_group)

            # For debugging
            msg = "Route for the tap configured"
            self.debug(msg)

        return self.port_number


    def establish_udp_connection(self,remote_endpoint, port):
        establish_connection_command = self._establish_connection_command(port)

        # upload command to connect.sh script
        shfile = os.path.join(self.app_home, "sw-connect.sh")
        self.node.upload_command(establish_connection_command,
                shfile = shfile,
                overwrite = False)

        # invoke connect script
        cmd = "bash %s" % shfile
        (out, err), proc = self.node.run(cmd, self.run_home,
                sudo  = True,
                stdout = "sw_stdout",
                stderr = "sw_stderr") 
             
        # check if execution errors occurred
        msg = "Failed to connect endpoints "
        if proc.poll():
            self.error(msg, out, err)
            raise RuntimeError, msg
    
        # Wait for pid file to be generated
        self._pid, self._ppid = self.node.wait_pid(self.run_home)
        
        # If the process is not running, check for error information
        # on the remote machine
        if not self._pid or not self._ppid:
            (out, err), proc = self.node.check_errors(self.run_home)
            # Out is what was written in the stderr file
            if err:
                msg = " Failed to start command '%s' " % command
                self.error(msg, out, err)
                raise RuntimeError, msg

        # For debugging
        msg = "Connection on port configured"
        self.debug(msg)


    def _establish_connection_command(self, port):
        """ Script to create the connection from a switch to a 
             remote endpoint
        """
        local_port_name = self.get('port_name')

        command = ["sliver-ovs"]
        command.append("set-remote-endpoint ")
        command.append("%s " % local_port_name)
        command.append("%s " % self.remote_ip)
        command.append("%s " % port)
        command = " ".join(command)
        command = self.replace_paths(command)
        return command
        
    def verify_connection(self):
        self.ovsswitch.ovs_status()

    def terminate_connection(self):
        return True

    def check_status(self):
        return self.node.status(self._pid, self._ppid)

    def do_deploy(self):
        """ Deploy the OVS port after the OVS Switch
        """

        if not self.ovsswitch or self.ovsswitch.state < ResourceState.READY:       
            self.debug("---- RESCHEDULING DEPLOY ---- OVSwitch state %s " % self.ovsswitch.state )  
            self.ec.schedule(self.reschedule_delay, self.deploy)
            return

        self.do_discover()
        self.do_provision()

        self.create_port()
        end_ip = self.ovsswitch.get('virtual_ip_pref').split('/')
        self.set("ip", end_ip[0])

        #Check the status of the OVS Switch
        self.ovsswitch.ovs_status()

        super(OVSPort, self).do_deploy()

    def do_release(self):
        """ Delete the port on the OVSwitch. It needs to wait for the tunnel
        to be released.
        """
        from nepi.resources.linux.udptunnel import LinuxUdpTunnel
        rm = self.get_connected(LinuxUdpTunnel.get_rtype())

        if rm and rm[0].state < ResourceState.STOPPED:
            self.ec.schedule(self.reschedule_delay, self.release)
            return 
            
        cmd = "sliver-ovs del_port %s" % self.get('port_name')
        (out, err), proc = self.node.run(cmd, self.ovsswitch.ovs_checks,
                sudo = True)

        msg = "Deleting the port %s" % self.get('port_name')
        self.info(msg)

        if proc.poll():
            self.error(msg, out, err)
            raise RuntimeError, msg

        super(OVSPort, self).do_release()

