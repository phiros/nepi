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

from nepi.execution.resource import clsinit_copy
from nepi.resources.ns3.ns3netdevice import NS3BaseNetDevice

@clsinit_copy
class NS3BaseFdNetDevice(NS3BaseNetDevice):
    _rtype = "abstract::ns3::FdNetDevice"

    @property
    def _rms_to_wait(self):
        rms = set([self.node])
        return rms

    def _configure_mac_address(self):
        # The wifimac is the one responsible for
        # configuring the MAC address
        pass

    def _connect_object(self):
        node = self.node
        if node and node.uuid not in self.connected:
            self.simulation.invoke(node.uuid, "AddDevice", self.uuid)
            self._connected.add(node.uuid)

    def _instantiate_object(self):
        """ just validate that the simulator is in real time
        mode, otherwise it is not going to work
        """

        mode = self.simulation.get("simulatorImplementationType")
        if mode != "ns3::RealtimeSimulatorImpl":
            msg = "The simulation must run in real time!!"
            self.error(msg)
            raise RuntimeError, msg
        
        super(NS3BaseFdNetDevice, self)._instantiate_object()

    def send_fd(self, fd):
        import passfd
        import socket
        
        address = self.simulation.invoke(self.uuid, "recvFD")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.connect(address)
        passfd.sendfd(sock, fd, '0')

