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
from nepi.execution.resource import clsinit_copy, ResourceState
from nepi.resources.linux.application import LinuxApplication

import os

@clsinit_copy
class LinuxRoute(LinuxApplication):
    _rtype = "linux::Route"
    _help = "Adds a route to the host using iptools "
    _backend = "linux"

    @classmethod
    def _register_attributes(cls):
        network = Attribute("network", "Network address", flags=Flags.Design)
        prefix = Attribute("prefix", "IP prefix length", flags=Flags.Design)
        nexthop = Attribute("nexthop", "Nexthop IP", flags=Flags.Design)

        cls._register_attribute(network)
        cls._register_attribute(prefix)
        cls._register_attribute(nexthop)

    def __init__(self, ec, guid):
        super(LinuxRoute, self).__init__(ec, guid)
        self._home = "route-%s" % self.guid
        self._device = None

    @property
    def device(self):
        if not self._device:
            from nepi.resources.linux.tap import LinuxTap
            from nepi.resources.linux.tun import LinuxTun
            from nepi.resources.linux.interface import LinuxInterface
            tap = self.get_connected(LinuxTap.get_rtype())
            tun = self.get_connected(LinuxTun.get_rtype())
            interface = self.get_connected(LinuxInterface.get_rtype())
            if tap: self._device = tap[0]
            elif tun: self._device = tun[0]
            elif interface: self._device = interface[0]
            else:
                raise RuntimeError, "linux::Routes must be connected to a "\
                        "linux::TAP, linux::TUN, or linux::Interface"
        return self._device

    @property
    def node(self):
        return self.device.node

    def upload_start_command(self):
        # We want to make sure the route is configured
        # before the deploy is over, so we execute the 
        # start script now and wait until it finishes. 
        command = self.get("command")
        command = self.replace_paths(command)

        shfile = os.path.join(self.app_home, "start.sh")
        self.node.run_and_wait(command, self.run_home,
            shfile = shfile,
            overwrite = True)

    def upload_sources(self):
        # upload stop.sh script
        stop_command = self.replace_paths(self._stop_command)

        self.node.upload(stop_command,
                os.path.join(self.app_home, "stop.sh"),
                text = True,
                # Overwrite file every time. 
                # The stop.sh has the path to the socket, which should change
                # on every experiment run.
                overwrite = True)

    def do_deploy(self):
        if not self.device or self.device.state < ResourceState.PROVISIONED:
            self.ec.schedule(self.reschedule_delay, self.deploy)
        else:
            if not self.get("command"):
                self.set("command", self._start_command)

            self.do_discover()
            self.do_provision()

            self.set_ready()

    def do_start(self):
        if self.state == ResourceState.READY:
            command = self.get("command")
            self.info("Starting command '%s'" % command)

            self.set_started()
        else:
            msg = " Failed to execute command '%s'" % command
            self.error(msg, out, err)
            raise RuntimeError, msg

    def do_stop(self):
        command = self.get('command') or ''
        
        if self.state == ResourceState.STARTED:
            self.info("Stopping command '%s'" % command)

            command = "bash %s" % os.path.join(self.app_home, "stop.sh")
            (out, err), proc = self.execute_command(command,
                    blocking = True)

            if err:
                msg = " Failed to stop command '%s' " % command
                self.error(msg, out, err)

            self.set_stopped()

    @property
    def _start_command(self):
        network = self.get("network")
        prefix = self.get("prefix")
        nexthop = self.get("nexthop")
        devicename = self.device.get("deviceName")

        command = []
        command.append("sudo -S ip route add %s/%s %s dev %s" % (
            self.get("network"),
            self.get("prefix"),
            "default" if not nexthop else "via %s" % nexthop,
            devicename))

        return " ".join(command)

    @property
    def _stop_command(self):
        network = self.get("network")
        prefix = self.get("prefix")
        nexthop = self.get("nexthop")
        devicename = self.device.get("deviceName")

        command = []
        command.append("sudo -S ip route del %s/%s %s dev %s" % (
            self.get("network"),
            self.get("prefix"),
            "default" if not nexthop else "via %s" % nexthop,
            devicename))

        return " ".join(command)

