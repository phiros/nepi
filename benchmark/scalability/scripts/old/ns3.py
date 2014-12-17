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

import os
import datetime
import ipaddr
import random
import psutil
import threading
import subprocess
import numpy
import time

from optparse import OptionParser

usage = ("usage: %prog -n <node_count> -a <app_count> -t <thread_count> "
        "-r <run> -d <delay> -o <opdelay> -R <results>")

parser = OptionParser(usage = usage)
parser.add_option("-n", "--node-count", dest="node_count", 
        help="Number of simulated nodes in the experiment", type="int")
parser.add_option("-a", "--app-count", dest="app_count", 
        help="Number of simulated applications in the experiment", type="int")
parser.add_option("-t", "--thread-count", dest="thread_count", 
        help="Number of threads processing experiment events", type="int")
parser.add_option("-r", "--run", dest="run", 
        help="Run numbber", type="int")
parser.add_option("-d", "--delay", dest="delay", 
        help="Re-scheduling delay", type="float")
parser.add_option("-o", "--opdelay", dest="opdelay", 
        help="Opetation processing delay", type="float")
parser.add_option("-R", "--results", dest="results", help="Results folder")

(options, args) = parser.parse_args()

results = options.results
node_count = options.node_count
app_count = options.app_count
thread_count = options.thread_count
run = options.run
clean_run = (run == 1)
opdelay = options.opdelay
delay = options.delay
reschedule_delay = "0s" # "%0.1fs" % delay

def get_nepi_revision():
    p = subprocess.Popen(["hg", "tip"], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    (stdout, stderr) = p.communicate()

    info = stdout.split("\n")
    changeset = info[0].split(":")[-1]

    return changeset

######### Resource consumption ################################################

cpu_count = psutil.NUM_CPUS
cpu_usage_deploy = []
cpu_usage_start = []

vmem = psutil.virtual_memory()
mem_total = vmem.total
mem_usage_deploy = []
mem_usage_start = []

stop_monitor_deploy = []
stop_monitor_start = []

def compute_estimator(samples):
    if len(samples) == 0:
        return 0,0,0

    x = numpy.array(samples)
    n = len(samples)
    std = x.std() 
    m = x.mean()

    return n, m, std

def monitor_resources(cpu_usage, mem_usage, stop):
    wait = 1

    while not stop:
        p = psutil.Process(os.getpid())
        cpu = p.get_cpu_percent(interval=1)
        cpu_usage.append(cpu)

        mem = p.get_memory_percent()
        mem_usage.append(mem)

        time.sleep(wait)

thread_monitor_deploy = threading.Thread(target=monitor_resources, 
        args=(cpu_usage_deploy, mem_usage_deploy, stop_monitor_deploy))

thread_monitor_start = threading.Thread(target=monitor_resources, 
        args=(cpu_usage_start, mem_usage_start, stop_monitor_start))

########## Declaration of resources #####################################

def add_linux_node(ec, clean_run):
    node = ec.register_resource("linux::Node")
    ec.set(node, "hostname", "localhost")
    #ec.set(node, "cleanExperiment", clean_run)
    ec.set(node, "cleanProcesses", True)

    return node

def add_node(ec, simu):
    node = ec.register_resource("ns3::Node")
    ec.set(node, "enableStack", True)
    ec.register_connection(node, simu)

    return node

def add_device(ec, node, ip, prefix):
    dev = ec.register_resource("ns3::CsmaNetDevice")
    ec.set(dev, "ip", ip)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(node, dev)
    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

def add_ping_app(ec, node, remote_ip):
    app = ec.register_resource("ns3::V4Ping")
    ec.set (app, "Remote", remote_ip)
    ec.set (app, "Verbose", True)
    ec.set (app, "Interval", "1s")
    ec.set (app, "StartTime", "0s")
    ec.set (app, "StopTime", "20s")
    ec.register_connection(app, node)

    return app

############## Experiment design and execution ################################

platform = "ns3"

# Set the number of threads. 
# NOTE: This must be done before instantiating the EC.
os.environ["NEPI_NTHREADS"] = str(thread_count)

# Create Experiment Controller:
exp_id = "%s_bench" % platform
ec = ExperimentController(exp_id)

# Add the physical node in which to run the simulation
lnode = add_linux_node(ec, clean_run)

# Add a simulation resource
simu = ec.register_resource("linux::ns3::Simulation")
ec.set(simu, "verbose", True)
ec.register_connection(simu, lnode)

# Add simulated nodes and applications
nodes = list()
apps = list()
devs = list()

ips = dict()

prefix = "16"
base_addr = "10.0.0.0/%s" % prefix
net = ipaddr.IPv4Network(base_addr)
host_itr = net.iterhosts()

for i in xrange(node_count):
    node = add_node(ec, simu)
    nodes.append(node)
    
    ip = host_itr.next()
    dev = add_device(ec, node, ip, prefix)
    devs.append(dev)

    ips[node] = ip

for nid in nodes:
    for j in xrange(app_count):
        # If there is only one node, ping itself. If there are more
        # choose one randomly.
        remote_ip = ips[nid]
        
        if len(nodes) > 1:
            choices = ips.values()
            choices.remove(remote_ip)
            remote_ip = random.choice(choices)

        app = add_ping_app(ec, node, remote_ip)
        apps.append(app)

chan = ec.register_resource("ns3::CsmaChannel")
ec.set(chan, "Delay", "0s")

for dev in devs:
    ec.register_connection(chan, dev)

# Deploy the experiment
zero_time = datetime.datetime.now()

# Launch thread to monitor CPU and memory usage
thread_monitor_deploy.start()

# Deploy experiment
ec.deploy()

# Wait until nodes and apps are deployed
ec.wait_deployed(nodes + apps + devs)

# Time to deploy
ttd_time = datetime.datetime.now()

# Launch thread to monitor CPU and memory usage
thread_monitor_start.start()

# Stop deploy monitoring thread
stop_monitor_deploy.append(0)

# Wait until the apps are finished
ec.wait_finished(apps)

# Time to finish
ttr_time = datetime.datetime.now()

# Stop deploy monitoring thread
stop_monitor_start.append(0)

# Do the experiment controller shutdown
ec.shutdown()

# Time to release
ttrel_time = datetime.datetime.now()

##################### Format performance information ##########################

# Get the failure level of the experiment (OK if no failure)
status = ec.failure_level
if status == 1:
    status = "OK"
elif status == 2:
    status = "RM_FAILURE"
else:
    status = "EC_FAILURE"

# Get time deltas in miliseconds
s2us = 1000000.0 # conversion factor s to microseconds = 10^6
s2ms = 1000.0 # conversion factor s to microseconds = 10^3

ttd = ttd_time - zero_time
ttdms =  (ttd.microseconds + ((ttd.seconds + ttd.days * 24 * 3600) * s2us)) / s2ms

ttr = (ttr_time - ttd_time)
ttrms =  (ttr.microseconds + ((ttr.seconds + ttr.days * 24 * 3600) * s2us)) / s2ms

ttrel = (ttrel_time - ttr_time)
ttrelms =  (ttrel.microseconds + ((ttrel.seconds + ttrel.days * 24 * 3600) * s2us)) / s2ms

############### Persist results

date = zero_time.strftime('%Y%m%d')

revision = get_nepi_revision()

filename = "%s_scalability_benchmark_rev_%s_%s.data" % (platform, revision, date)
filename = os.path.join(results, filename)

if not os.path.exists(filename):
    f = open(filename, "w")
    f.write("time|platform|cpu_count(%)|cpu_deploy(%)|cpu_start|"
    "mem_total(B)|mem_deploy(%)|mem_starts(%)|opdelay(s)|scheddelay(s)|run#|"
    "node_count|app_count|thread_count|TTD(ms)|TTR(ms)|TTREL(ms)|status\n")
else:
    f = open(filename, "a")

n,m,std = compute_estimator(cpu_usage_deploy)
cpu_deploy = "%d,%0.2f,%0.2f" % (n,m,std)

n,m,std = compute_estimator(cpu_usage_start)
cpu_start = "%d,%0.2f,%0.2f" % (n,m,std)

n,m,std = compute_estimator(mem_usage_deploy)
mem_deploy = "%d,%0.2f,%0.2f" % (n,m,std)

n,m,std = compute_estimator(mem_usage_start)
mem_start = "%d,%0.2f,%0.2f" % (n,m,std)

timestmp = zero_time.strftime('%Y%m%d %H:%M:%S')

f.write("%s|%s|%d|%s|%s|%d|%s|%s|%0.1f|%0.1f|%d|%d|%d|%d|%d|%d|%d|%s\n" % (
    timestmp,
    platform,
    cpu_count,
    cpu_deploy,
    cpu_start,
    mem_total,
    mem_deploy,
    mem_start,
    opdelay,
    delay,
    run,
    node_count,
    app_count,
    thread_count,
    ttdms,
    ttrms,
    ttrelms,
    status
    ))

f.close()

