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

from nepi.execution.attribute import Attribute, Flags, Types
from nepi.execution.resource import clsinit_copy
from nepi.resources.ns3.ns3base import NS3Base

import socket

@clsinit_copy
class NS3BasePipeChannel(NS3Base):
    """ Interconnects two FdNetDevices with a PIPE
    """
    _rtype = "ns3::PipeChannel"

    def __init__(self, ec, guid):
        super(NS3BasePipeChannel, self).__init__(ec, guid)
        self._devices = None

    @property
    def devices(self):
        if not self._devices:
            from nepi.resources.ns3.ns3fdnetdevice import NS3BaseFdNetDevice
            devices = self.get_connected(NS3BaseFdNetDevice.get_rtype())
            if not devices or len(devices) != 2: 
                msg = "PipeChannel must be connected to exactly to two FdNetDevices"
                self.error(msg)
                raise RuntimeError, msg

            self._devices = devices
        
        return self._devices

    @property
    def node(self):
        return self.devices[0].node

    @property
    def _rms_to_wait(self):
        rms = set(self.devices)
        return rms

    def _instantiate_object(self):
        """ The pipe channel does not really exists as an ns-3 object.
        Do nothing.
        """
        pass

    def _connect_object(self):
        dev1 = self.devices[0]
        dev2 = self.devices[1]

        if dev1.uuid not in self.connected and dev2.uuid not in self.connected:
            (s0, s1) = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)
            
            dev1.send_fd(s0)

            self._connected.add(dev1.uuid)
            dev1._connected.add(self.uuid)

            dev2.send_fd(s1)

            self._connected.add(dev2.uuid)
            dev2._connected.add(self.uuid)


