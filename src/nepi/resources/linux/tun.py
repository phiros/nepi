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

from nepi.execution.resource import clsinit_copy
from nepi.resources.linux.tap import LinuxTap

import os

@clsinit_copy
class LinuxTun(LinuxTap):
    _rtype = "linux::Tun"
    _help = "Creates a TUN device on a Linux host"
    _backend = "linux"

    def __init__(self, ec, guid):
        super(LinuxTun, self).__init__(ec, guid)
        self._home = "tun-%s" % self.guid

    @property
    def sock_name(self):
        return os.path.join(self.run_home, "tun.sock")
    
    @property
    def vif_type(self):
        return "IFF_TUN"

    @property
    def vif_type_flag(self):
        return LinuxTap.IFF_TAP

    @property
    def vif_prefix(self):
        return "tun"


