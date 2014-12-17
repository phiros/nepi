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
from nepi.execution.resource import ResourceManager, ResourceState, \
        clsinit_copy

import os
import socket
import struct
import fcntl

@clsinit_copy
class TapFdLink(ResourceManager):
    """ Interconnects a TAP or TUN Linux device to a FdNetDevice
    """
    _rtype = "linux::ns3::TapFdLink"

    def __init__(self, ec, guid):
        super(TapFdLink, self).__init__(ec, guid)
        self._tap = None
        self._fdnetdevice = None
        self._fd = None

    @property
    def fdnetdevice(self):
        if not self._fdnetdevice:
            from nepi.resources.ns3.ns3fdnetdevice import NS3BaseFdNetDevice
            devices = self.get_connected(NS3BaseFdNetDevice.get_rtype())
            if not devices or len(devices) != 1: 
                msg = "TapFdLink must be connected to exactly one FdNetDevices"
                self.error(msg)
                raise RuntimeError, msg

            self._fdnetdevice = devices[0]
        
        return self._fdnetdevice

    @property
    def fdnode(self):
        return self.fdnetdevice.node

    @property
    def tap(self):
        if not self._tap:
            from nepi.resources.linux.tap import LinuxTap
            devices = self.get_connected(LinuxTap.get_rtype())
            if not devices or len(devices) != 1: 
                msg = "TapFdLink must be connected to exactly one LinuxTap"
                self.error(msg)
                raise RuntimeError, msg

            self._tap = devices[0]
        
        return self._tap

    @property
    def tapnode(self):
        return self.tap.node

    def do_provision(self):
        tap = self.tap
        fdnetdevice = self.fdnetdevice

        vif_name = self.ec.get(tap.guid, "deviceName")
        vif_type = tap.vif_type_flag
        pi = self.ec.get(tap.guid, "pi")

        self._fd = self.open_tap(vif_name, vif_type, pi)

        fdnetdevice.send_fd(self._fd)

        super(TapFdLink, self).do_provision()

    def do_deploy(self):
        if self.tap.state < ResourceState.READY or \
                self.fdnetdevice.state < ResourceState.READY:
            self.ec.schedule(self.reschedule_delay, self.deploy)
        else:
            self.do_discover()
            self.do_provision()

            super(TapFdLink, self).do_deploy()

    def open_tap(self, vif_name, vif_type, pi):
        IFF_NO_PI = 0x1000
        TUNSETIFF = 0x400454ca

        flags = 0
        flags |= vif_type

        if not pi:
            flags |= IFF_NO_PI

        fd = os.open("/dev/net/tun", os.O_RDWR)

        err = fcntl.ioctl(fd, TUNSETIFF, struct.pack("16sH", vif_name, flags))
        if err < 0:
            os.close(fd)
            raise RuntimeError("Could not configure device %s" % vif_name)

        return fd


