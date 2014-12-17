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

from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState

import os
import time
import argparse

# Set experiment for broadcast or vod mode

parser = argparse.ArgumentParser(description='NEPI VoD/Broadcast experiment')
parser.add_argument('-m', '--mode', help='Set vlc mode, possible values <vod> or <broadcast>', required=True)
args = parser.parse_args()

mode = args.mode

# Create the entity Experiment Controller

exp_id = "vod_exp"
ec = ExperimentController(exp_id)

# Define SFA credentials

slicename = 'ple.inria.nepi'
sfauser = 'ple.inria.aquereilhac'
sfaPrivateKey = '/home/alina/.sfi/aquereilhac.pkey'

# Functions for nodes and ifaces registration

def create_planetlab_node(ec, host):
    node = ec.register_resource("planetlab::sfa::Node")
    ec.set(node, "hostname", host)
    ec.set(node, "username", "inria_nepi")
    ec.set(node, "sfauser", sfauser)
    ec.set(node, "sfaPrivateKey", sfaPrivateKey)
    ec.set(node, 'cleanExperiment', True)
    return node

def create_omf_node(ec, host):
    node = ec.register_resource("wilabt::sfa::Node")
    ec.set(node, "host", host)
    ec.set(node, "slicename", slicename)
    ec.set(node, "sfauser", sfauser)
    ec.set(node, "sfaPrivateKey", sfaPrivateKey)
    ec.set(node, "gatewayUser", "nepi")
    ec.set(node, "gateway", "bastion.test.iminds.be")
    ec.set(node, "disk_image", 'NepiVlcOMF6Baseline')
    ec.set(node, 'xmppServer', "xmpp.ilabt.iminds.be")
    ec.set(node, 'xmppUser', "nepi")
    ec.set(node, 'xmppPort', "5222")
    ec.set(node, 'xmppPassword', "1234")
    return node

def create_omf_iface(ec, ip, node):
    iface = ec.register_resource("omf::WifiInterface")
    ec.set(iface, 'name', 'wlan0')
    ec.set(iface, 'mode', "adhoc")
    ec.set(iface, 'hw_mode', "g")
    ec.set(iface, 'essid', "vlc")
    ec.set(iface, 'ip', ip)
    ec.register_connection(iface, node)
    return iface

# Register Internet VLC server

video_server = create_planetlab_node(ec, 'planetlab3.xeno.cl.cam.ac.uk')

# Register wifi media center and client nodes

wifi_center = create_omf_node(ec, 'zotacB1')
client1 = create_omf_node(ec, 'zotacB3')
client2 = create_omf_node(ec, 'zotacB5')
client3 = create_omf_node(ec, 'zotacC1')
client4 = create_omf_node(ec, 'zotacC3')
client5 = create_omf_node(ec, 'zotacB2')

omf_nodes = [wifi_center, client1, client2, client3, client4, client5]

# Register ifaces in wireless nodes

iface_center = create_omf_iface(ec, "192.168.0.1/24", wifi_center)
iface_client1 = create_omf_iface(ec, "192.168.0.2/24", client1)
iface_client2 = create_omf_iface(ec, "192.168.0.3/24", client2)
iface_client3 = create_omf_iface(ec, "192.168.0.4/24", client3)
iface_client4 = create_omf_iface(ec, "192.168.0.5/24", client4)
iface_client5 = create_omf_iface(ec, "192.168.0.6/24", client5)

omf_ifaces = [iface_center, iface_client1, iface_client2, iface_client3, iface_client4, iface_client5]

# Register channel

chan = ec.register_resource("omf::Channel")
ec.set(chan, 'channel', "6")

# Register connection ifaces - channel

ec.register_connection(iface_center, chan)
ec.register_connection(iface_client1, chan)
ec.register_connection(iface_client2, chan)
ec.register_connection(iface_client3, chan)
ec.register_connection(iface_client4, chan)
ec.register_connection(iface_client5, chan)

resources = [video_server] + omf_nodes + omf_ifaces + [chan]

# Deploy physical resources and wait until they become provisioned

ec.deploy(resources)

ec.wait_deployed(resources)
  
time.sleep(3)

# Functions for applications registration in the nodes

def create_vlc_server(ec, video_server, mode):
    vlc_server = ec.register_resource("linux::Application")
    ec.set(vlc_server, "depends", "vlc")
    ec.set(vlc_server, "sources", "examples/omf/demo_openlab/big_buck_bunny_240p_mpeg4_lq.ts")
    # Depending on the mode selected to run the experiment, 
    # different configuation files and command to run are
    # uploaded to the server
    if mode == 'vod':
        ec.set(vlc_server, "files", "examples/omf/demo_openlab/conf_VoD.vlm")
        ec.set(vlc_server, "command", "sudo -S dbus-uuidgen --ensure ; cvlc --vlm-conf ${SHARE}/conf_VoD.vlm --rtsp-host 128.232.103.203:5554 2>/tmp/logpl.txt")
    elif mode == 'broadcast':
        ec.set(vlc_server, "files", "examples/omf/demo_openlab/conf_Broadcast.vlm")
        ec.set(vlc_server, "command", "sudo -S dbus-uuidgen --ensure ; cvlc --vlm-conf ${SHARE}/conf_Broadcast.vlm --rtsp-host 128.232.103.203:5554 2>/tmp/logpl.txt")
    ec.register_connection(video_server, vlc_server)
    return vlc_server

def create_omf_app(ec, command, node):
    app = ec.register_resource("omf::Application")
    ec.set(app, 'command', command)
    ec.register_connection(app, node)
    return app


# Run the VLC server in the Planetlab node

vlc_server = create_vlc_server(ec, video_server, mode)

# Upload configuration to the wifi media center and run VLC

if mode == 'vod':
    update_file_wificenter = "echo -e 'new BUNNY vod enabled\\n"\
       "setup BUNNY input rtsp://128.232.103.203:5554/BUNNY' > /root/wificenter.vlm"
    command_wificenter =  "/root/vlc/vlc-1.1.13/cvlc --vlm-conf /root/wificenter.vlm --rtsp-host 192.168.0.1:5554"
elif mode == 'broadcast':
    update_file_wificenter = "echo -e 'new BUNNY broadcast enabled loop\\n"\
       "setup BUNNY input rtsp://128.232.103.203:8554/BUNNY\\n"\
       "setup BUNNY output #rtp{access=udp,mux=ts,sdp=rtsp://0.0.0.0:8554/BUNNY}\\n\\n"\
       "new test_sched schedule enabled\\n"\
       "setup test_sched append control BUNNY play' > /root/wificenter.vlm"
    command_wificenter =  "/root/vlc/vlc-1.1.13/cvlc --vlm-conf /root/wificenter.vlm --rtsp-host 192.168.0.1:8554"

upload_conf = create_omf_app(ec, update_file_wificenter , wifi_center)
vlc_wificenter = create_omf_app(ec, command_wificenter , wifi_center)

ec.register_condition(upload_conf, ResourceAction.START, vlc_server, ResourceState.STARTED , "2s")
ec.register_condition(vlc_wificenter, ResourceAction.START, upload_conf, ResourceState.STARTED , "2s")

# measurements in video server (PL node)
measure_videoserver = ec.register_resource("linux::Application")
ec.set(measure_videoserver, "depends", "tcpdump")
ec.set(measure_videoserver, "sudo", True)
command = "tcpdump -i eth0 not arp -n -w /tmp/capplserver_%s.pcap" % ("$(date +'%Y%m%d%H%M%S')")
ec.set(measure_videoserver, "command", command)
ec.register_connection(measure_videoserver, video_server)

# Deploy servers
ec.deploy([vlc_server, upload_conf, vlc_wificenter, measure_videoserver])

ec.wait_started([vlc_server, upload_conf, vlc_wificenter, measure_videoserver])

time.sleep(3)

def deploy_experiment(ec, clients, wifi_center):

    # measurements in transmitter eth0
    command_measure_wificentereth0 = "/usr/sbin/tcpdump -i eth0 not arp -n -w /tmp/capwificen_eth0_%s_%s.pcap" % (len(clients), "$(date +'%Y%m%d%H%M%S')")
    measure_wificentereth0 = create_omf_app(ec, command_measure_wificentereth0, wifi_center)
    ec.register_condition(measure_wificentereth0, ResourceAction.STOP, measure_wificentereth0, ResourceState.STARTED , "65s")

    # measurements in transmitter wlan0
    command_measure_wificenterwlan0 = "/usr/sbin/tcpdump -i wlan0 not arp -n -w /tmp/capwificen_wlan0_%s_%s.pcap" % (len(clients), "$(date +'%Y%m%d%H%M%S')")
    measure_wificenterwlan0 = create_omf_app(ec, command_measure_wificenterwlan0, wifi_center)
    ec.register_condition(measure_wificenterwlan0, ResourceAction.STOP, measure_wificenterwlan0, ResourceState.STARTED , "65s")

    # kill tcpdumps in wificenter
    command_kill_measure_wificentereth0 = "killall /usr/sbin/tcpdump"
    kill_measure_wificentereth0 = create_omf_app(ec, command_kill_measure_wificentereth0, wifi_center)
    ec.register_condition(kill_measure_wificentereth0, ResourceAction.START, measure_wificentereth0, ResourceState.STARTED , "65s")
    ec.register_condition(kill_measure_wificentereth0, ResourceAction.STOP, kill_measure_wificentereth0, ResourceState.STARTED , "2s")


    apps = [measure_wificentereth0, measure_wificenterwlan0, kill_measure_wificentereth0]
    delay = '2s'
    for client in clients:
        client_host = ec.get(client, 'host').split('.')[0]
        # measurements in clients
        command_measure_client = "/usr/sbin/tcpdump -i wlan0 not arp -n -w /tmp/capcli_%s_%s_%s.pcap" % (client_host, len(clients), "$(date +'%Y%m%d%H%M%S')")
        # run vlc client
        if mode == 'broadcast':
            command_client =  "/root/vlc/vlc-1.1.13/cvlc rtsp://192.168.0.1:8554/BUNNY --sout=file/ts:%s_%s_%s.ts 2>/tmp/logcli.txt" % (client_host, len(clients), "$(date +'%Y%m%d%H%M%S')")
        elif mode == 'vod':    
            command_client =  "/root/vlc/vlc-1.1.13/cvlc rtsp://192.168.0.1:5554/BUNNY --sout=file/ts:%s_%s_%s.ts 2>/tmp/logcli.txt" % (client_host, len(clients), "$(date +'%Y%m%d%H%M%S')")

        # kill vlc client and tcpdump
        command_client_killvlc = "killall vlc vlc_app"
        command_client_killtcp = "killall /usr/sbin/tcpdump"

        run_client = create_omf_app(ec, command_client, client)
        measure_client = create_omf_app(ec, command_measure_client, client)
        kill_clientvlc = create_omf_app(ec, command_client_killvlc, client)
        kill_clienttcp = create_omf_app(ec, command_client_killtcp, client)
        ec.register_condition(run_client, ResourceAction.START, measure_client, ResourceState.STARTED , delay)
        ec.register_condition([run_client, measure_client], ResourceAction.STOP, run_client, ResourceState.STARTED , "60s")
        ec.register_condition(kill_clientvlc, ResourceAction.START, run_client, ResourceState.STARTED , "60s")
        ec.register_condition(kill_clienttcp, ResourceAction.START, measure_client, ResourceState.STARTED , "60s")
        ec.register_condition(kill_clientvlc, ResourceAction.STOP, kill_clientvlc, ResourceState.STARTED , "2s")
        ec.register_condition(kill_clienttcp, ResourceAction.STOP, kill_clienttcp, ResourceState.STARTED , "2s")
        apps.append(run_client)
        apps.append(measure_client)
        apps.append(kill_clientvlc)
        apps.append(kill_clienttcp)
    
    return apps

#################
## 1 client run #
#################

apps1 = deploy_experiment(ec, [client1], wifi_center)

ec.deploy(apps1)
ec.wait_finished(apps1)

################
# 3 client run #
################

#apps3 = deploy_experiment(ec, [client1, client2, client3], wifi_center)
#
#ec.deploy(apps3)
#ec.wait_finished(apps3)

################
# 5 client run #
################
#
#apps5 = deploy_experiment(ec, [client1, client2, client3, client4, client5], wifi_center)

#ec.deploy(apps5)
#ec.wait_finished(apps5)

ec.shutdown()

# End
