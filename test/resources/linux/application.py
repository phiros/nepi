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
# Author: Alina Quereilhac <alina.quereilhac@inria.fr>

from nepi.execution.ec import ExperimentController 
from nepi.execution.resource import ResourceState, ResourceAction
from nepi.execution.trace import TraceAttr

from test_utils import skipIfNotAlive, skipInteractive

import os
import shutil
import time
import tempfile
import unittest

class LinuxApplicationTestCase(unittest.TestCase):
    def setUp(self):
        self.fedora_host = "nepi2.pl.sophia.inria.fr"
        self.fedora_user = "inria_nepi"

        self.ubuntu_host = "roseval.pl.sophia.inria.fr"
        self.ubuntu_user = "inria_nepi"
        
        self.target = "nepi5.pl.sophia.inria.fr"

    @skipIfNotAlive
    def t_stdout(self, host, user):

        ec = ExperimentController(exp_id = "test-stdout")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        app = ec.register_resource("linux::Application")
        cmd = "echo 'HOLA'"
        ec.set(app, "command", cmd)
        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished(app)

        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(ec.state(app) == ResourceState.STOPPED)

        stdout = ec.trace(app, "stdout")
        self.assertTrue(stdout.strip() == "HOLA")

        ec.shutdown()

    @skipIfNotAlive
    def t_ping(self, host, user):

        ec = ExperimentController(exp_id = "test-ping")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        app = ec.register_resource("linux::Application")
        cmd = "ping -c5 %s" % self.target 
        ec.set(app, "command", cmd)
        
        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished(app)

        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(ec.state(app) == ResourceState.STOPPED)

        stdout = ec.trace(app, "stdout")
        size = ec.trace(app, "stdout", attr = TraceAttr.SIZE)
        self.assertEquals(len(stdout), size)
        
        block = ec.trace(app, "stdout", attr = TraceAttr.STREAM, block = 5, offset = 1)
        self.assertEquals(block, stdout[5:10])

        path = ec.trace(app, "stdout", attr = TraceAttr.PATH)
        rm = ec.get_resource(app)
        p = os.path.join(rm.run_home, "stdout")
        self.assertEquals(path, p)

        ec.shutdown()

    @skipIfNotAlive
    def t_code(self, host, user):

        ec = ExperimentController(exp_id = "tests-code")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)
        
        prog = """#include <stdio.h>

int
main (void)
{
    printf ("Hello, world!\\n");
    return 0;
}
"""
        cmd = "${RUN_HOME}/hello" 
        build = "gcc -Wall -x c ${APP_HOME}/code -o hello" 

        app = ec.register_resource("linux::Application")
        ec.set(app, "command", cmd)
        ec.set(app, "code", prog)
        ec.set(app, "depends", "gcc")
        ec.set(app, "build", build)
        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished(app)

        out = ec.trace(app, 'stdout')
        self.assertEquals(out, "Hello, world!\n")

        ec.shutdown()

    @skipIfNotAlive
    def t_concurrency(self, host, user):

        ec = ExperimentController(exp_id="test-concurrency")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        apps = list()
        for i in xrange(50):
            app = ec.register_resource("linux::Application")
            cmd = "ping -c5 %s" % self.target 
            ec.set(app, "command", cmd)
            ec.register_connection(app, node)
            apps.append(app)

        ec.deploy()

        ec.wait_finished(apps)

        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(
               all([ec.state(guid) == ResourceState.STOPPED \
                for guid in apps])
                )

        for app in apps:
            stdout = ec.trace(app, 'stdout')
            size = ec.trace(app, 'stdout', attr = TraceAttr.SIZE)
            self.assertEquals(len(stdout), size)
            
            block = ec.trace(app, 'stdout', attr = TraceAttr.STREAM, block = 5, offset = 1)
            self.assertEquals(block, stdout[5:10])

            path = ec.trace(app, 'stdout', attr = TraceAttr.PATH)
            rm = ec.get_resource(app)
            p = os.path.join(rm.run_home, 'stdout')
            self.assertEquals(path, p)

        ec.shutdown()

    @skipIfNotAlive
    def t_condition(self, host, user, depends):

        ec = ExperimentController(exp_id="test-condition")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        server = ec.register_resource("linux::Application")
        cmd = "echo 'HOLA' | nc -l 3333"
        ec.set(server, "command", cmd)
        ec.set(server, "depends", depends)
        ec.register_connection(server, node)

        client = ec.register_resource("linux::Application")
        cmd = "nc 127.0.0.1 3333"
        ec.set(client, "command", cmd)
        ec.register_connection(client, node)

        ec.register_condition(client, ResourceAction.START, server, ResourceState.STARTED)

        apps = [client, server]
        
        ec.deploy()

        ec.wait_finished(apps)

        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(ec.state(server) == ResourceState.STOPPED)
        self.assertTrue(ec.state(client) == ResourceState.STOPPED)

        stdout = ec.trace(client, "stdout")
        self.assertTrue(stdout.strip() == "HOLA")

        ec.shutdown()

    @skipIfNotAlive
    def t_http_sources(self, host, user):

        ec = ExperimentController(exp_id="test-http-sources")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        sources = "http://yans.pl.sophia.inria.fr/code/nef/archive/tip.tar.gz;" \
                "http://yans.pl.sophia.inria.fr/code/nef/raw-file/8ace577d4079/src/nef/images/menu/connect.png"

        app = ec.register_resource("linux::Application")
        ec.set(app, "sources", sources)

        command = "ls ${SRC}"
        ec.set(app, "command", command)

        ec.register_connection(app, node)


        ec.deploy()

        ec.wait_finished([app])

        self.assertTrue(ec.state(node) == ResourceState.STARTED)
        self.assertTrue(ec.state(app) == ResourceState.STOPPED)

        exitcode = ec.trace(app, "deploy_exitcode")
        self.assertTrue(exitcode.strip() == "0")
        
        out = ec.trace(app, "deploy_stdout")
        self.assertTrue(out.find("tip.tar.gz") > -1)
        self.assertTrue(out.find("connect.png") > -1)

        stdout = ec.trace(app, "stdout")
        self.assertTrue(stdout.find("tip.tar.gz") > -1)
        self.assertTrue(stdout.find("connect.png") > -1)

        ec.shutdown()

    @skipIfNotAlive
    def t_xterm(self, host, user):

        ec = ExperimentController(exp_id="test-xterm")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        app = ec.register_resource("linux::Application")
        ec.set(app, "command", "xterm")
        ec.set(app, "depends", "xterm")
        ec.set(app, "forwardX11", True)

        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished([app])

        self.assertTrue(ec.state(app) == ResourceState.STOPPED)

        ec.shutdown()

    @skipIfNotAlive
    def t_copy_files(self, host, user):
        # create some temp files and directories to copy
        dirpath = tempfile.mkdtemp()
        f = tempfile.NamedTemporaryFile(dir=dirpath, delete=False)
        f.close()
      
        f1 = tempfile.NamedTemporaryFile(delete=False)
        f1.close()
        f1.name

        ec = ExperimentController(exp_id="test-copyfile")
        
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", host)
        ec.set(node, "username", user)
        ec.set(node, "cleanExperiment", True)
        ec.set(node, "cleanProcesses", True)

        app = ec.register_resource("linux::Application")
        ec.set(app, "command", "ls ${SRC}")
        ec.set(app, "sources", "%s;%s" % (dirpath, f1.name))
        ec.register_connection(app, node)

        ec.deploy()

        ec.wait_finished([app])

        stdout = ec.trace(app, "stdout")
        
        self.assertTrue(stdout.find(os.path.basename(dirpath)) > -1)
        self.assertTrue(stdout.find(os.path.basename(f1.name)) > -1)

        ec.shutdown()
        
        os.remove(f1.name)
        shutil.rmtree(dirpath)

    def test_stdout_fedora(self):
        self.t_stdout(self.fedora_host, self.fedora_user)

    def test_stdout_ubuntu(self):
        self.t_stdout(self.ubuntu_host, self.ubuntu_user)

    def test_ping_fedora(self):
        self.t_ping(self.fedora_host, self.fedora_user)

    def test_ping_ubuntu(self):
        self.t_ping(self.ubuntu_host, self.ubuntu_user)

    def test_concurrency_fedora(self):
        self.t_concurrency(self.fedora_host, self.fedora_user)

    def test_concurrency_ubuntu(self):
        self.t_concurrency(self.ubuntu_host, self.ubuntu_user)

    def test_condition_fedora(self):
        self.t_condition(self.fedora_host, self.fedora_user, "nc")

    def test_condition_ubuntu(self):
        self.t_condition(self.ubuntu_host, self.ubuntu_user, "netcat")

    def test_http_sources_fedora(self):
        self.t_http_sources(self.fedora_host, self.fedora_user)

    def test_http_sources_ubuntu(self):
        self.t_http_sources(self.ubuntu_host, self.ubuntu_user)

    def test_code_fedora(self):
        self.t_code(self.fedora_host, self.fedora_user)

    def test_code_ubuntu(self):
        self.t_code(self.ubuntu_host, self.ubuntu_user)

    @skipInteractive
    def test_xterm_ubuntu(self):
        """ Interactive test. Should not run automatically """
        self.t_xterm(self.ubuntu_host, self.ubuntu_user)

    def test_copy_files_fedora(self):
        self.t_copy_files(self.fedora_host, self.fedora_user)

    def test_copy_files_ubuntu(self):
        self.t_copy_files(self.ubuntu_host, self.ubuntu_user)

if __name__ == '__main__':
    unittest.main()

