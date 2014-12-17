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

from nepi.execution.attribute import Attribute, Flags, Types
from nepi.execution.resource import clsinit_copy, ResourceState
from nepi.resources.linux.tunnel import LinuxTunnel
from nepi.util.sshfuncs import ProcStatus
from nepi.util.timefuncs import tnow, tdiffsec

import os
import socket
import time

@clsinit_copy
class LinuxUdpTunnel(LinuxTunnel):
    _rtype = "linux::UdpTunnel"
    _help = "Constructs a tunnel between two Linux endpoints using a UDP connection "
    _backend = "linux"

    @classmethod
    def _register_attributes(cls):
        cipher = Attribute("cipher",
               "Cipher to encript communication. "
                "One of PLAIN, AES, Blowfish, DES, DES3. ",
                default = None,
                allowed = ["PLAIN", "AES", "Blowfish", "DES", "DES3"],
                type = Types.Enumerate, 
                flags = Flags.Design)

        cipher_key = Attribute("cipherKey",
                "Specify a symmetric encryption key with which to protect "
                "packets across the tunnel. python-crypto must be installed "
                "on the system." ,
                flags = Flags.Design)

        txqueuelen = Attribute("txQueueLen",
                "Specifies the interface's transmission queue length. "
                "Defaults to 1000. ", 
                type = Types.Integer, 
                flags = Flags.Design)

        bwlimit = Attribute("bwLimit",
                "Specifies the interface's emulated bandwidth in bytes "
                "per second.",
                type = Types.Integer, 
                flags = Flags.Design)

        cls._register_attribute(cipher)
        cls._register_attribute(cipher_key)
        cls._register_attribute(txqueuelen)
        cls._register_attribute(bwlimit)

    def __init__(self, ec, guid):
        super(LinuxUdpTunnel, self).__init__(ec, guid)
        self._home = "udp-tunnel-%s" % self.guid
        self._pids = dict()

    def log_message(self, msg):
        return " guid %d - udptunnel %s - %s - %s " % (self.guid, 
                self.endpoint1.node.get("hostname"), 
                self.endpoint2.node.get("hostname"), 
                msg)

    def get_endpoints(self):
        """ Returns the list of RM that are endpoints to the tunnel 
        """
        connected = []
        for guid in self.connections:
            rm = self.ec.get_resource(guid)
            if hasattr(rm, "initiate_udp_connection"):
                connected.append(rm)
        return connected

    def initiate_connection(self, endpoint, remote_endpoint):
        cipher = self.get("cipher")
        cipher_key = self.get("cipherKey")
        bwlimit = self.get("bwLimit")
        txqueuelen = self.get("txQueueLen")
        connection_app_home = self.app_home(endpoint)
        connection_run_home = self.run_home(endpoint)

        port = endpoint.initiate_udp_connection(
                remote_endpoint, 
                connection_app_home,
                connection_run_home, 
                cipher, cipher_key, bwlimit, txqueuelen)

        return port

    def establish_connection(self, endpoint, remote_endpoint, port):
        endpoint.establish_udp_connection(remote_endpoint, port)

    def verify_connection(self, endpoint, remote_endpoint):
        endpoint.verify_connection()

    def terminate_connection(self, endpoint, remote_endpoint):
        endpoint.terminate_connection()

    def check_state_connection(self):
        # Make sure the process is still running in background
        # No execution errors occurred. Make sure the background
        # process with the recorded pid is still running.

        status1 = self.endpoint1.check_status()
        status2 = self.endpoint2.check_status()

        if status1 == ProcStatus.FINISHED and \
                status2 == ProcStatus.FINISHED:

            # check if execution errors occurred
            (out1, err1), proc1 = self.endpoint1.node.check_errors(
                    self.run_home(self.endpoint1))

            (out2, err2), proc2 = self.endpoint2.node.check_errors(
                    self.run_home(self.endpoint2))

            if err1 or err2: 
                msg = "Error occurred in tunnel"
                self.error(msg, err1, err2)
                self.fail()
            else:
                self.set_stopped()

    def wait_local_port(self, endpoint):
        """ Waits until the local_port file for the endpoint is generated, 
        and returns the port number 
        
        """
        return self.wait_file(endpoint, "local_port")

    def wait_result(self, endpoint):
        """ Waits until the return code file for the endpoint is generated 
        
        """ 
        return self.wait_file(endpoint, "ret_file")
 
    def wait_file(self, endpoint, filename):
        """ Waits until file on endpoint is generated """
        result = None
        delay = 1.0

        for i in xrange(20):
            (out, err), proc = endpoint.node.check_output(
                    self.run_home(endpoint), filename)

            if out:
                result = out.strip()
                break
            else:
                time.sleep(delay)
                delay = delay * 1.5
        else:
            msg = "Couldn't retrieve %s" % filename
            self.error(msg, out, err)
            raise RuntimeError, msg

        return result

