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

import datetime
import imp
import numpy
import os
import platform as pltfrm
import psutil
import random
import socket
import subprocess
import threading
import time

from optparse import OptionParser

def parse_args():
    usage = ("usage: %prog -n <node_count> -a <app_count> -t <thread_count> "
            "-r <run> -d <delay> -o <opdelay> -p <platform> -R <results-dir> ")

    parser = OptionParser(usage = usage)
    parser.add_option("-p", "--platform", dest="platform", 
        help="Platform to benchmark. One of dummy|ns3|dce|planetlab|omf6")
    parser.add_option("-n", "--node-count", dest="node_count", 
            help="Number of simulated nodes in the experiment", type="int")
    parser.add_option("-a", "--app-count", dest="app_count", 
            help="Number of simulated applications in the experiment", type="int")
    parser.add_option("-t", "--thread-count", dest="thread_count", 
            help="Number of threads processing experiment events", type="int")
    parser.add_option("-r", "--run", dest="run", help="Run number", type="int")
    parser.add_option("-d", "--delay", dest="delay", 
            help="Re-scheduling delay", type="float")
    parser.add_option("-o", "--opdelay", dest="opdelay", 
            help="Operation processing delay", type="float")
    parser.add_option("-R", "--results", dest="results", help="Results folder")

    (options, args) = parser.parse_args()

    node_count = options.node_count
    app_count = options.app_count
    thread_count = options.thread_count
    run = options.run
    opdelay = options.opdelay
    delay = options.delay
    platform = options.platform
    results = options.results

    return (node_count, app_count, thread_count, run, opdelay, delay, 
            platform, results)

def get_nepi_revision():
    p = subprocess.Popen(["hg", "tip"], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    (stdout, stderr) = p.communicate()

    info = stdout.split("\n")
    changeset = info[0].split(":")[-1]

    return changeset

######### Resource consumption ################################################

def compute_estimator(samples):
    if len(samples) == 0:
        return 0,0,0

    x = numpy.array(samples)
    n = len(samples)
    std = x.std() 
    m = x.mean()

    return n, m, std

def monitor_resources(cpu_usage, mem_usage, stop):
    wait = 0.5 
    p = psutil.Process(os.getpid())

    while not stop:
        cpu = p.get_cpu_percent(interval=0.1)
        cpu_usage.append(cpu)

        mem = p.get_memory_percent()
        mem_usage.append(mem)

        time.sleep(wait)

########## Persist results ####################################################

def persist_results(ec, platform, results, cpu_usage_deploy, cpu_usage_execution, 
        cpu_usage_release, mem_usage_deploy, mem_usage_execution, 
        mem_usage_release, ttd_time, ttdf_time, ttef_time, 
        tts_time, ttsf_time):

    ##################### Experiment finalization status

    # Get the failure level of the experiment (OK if no failure)
    status = ec.failure_level
    if status == 1:
        status = "OK"
    elif status == 2:
        status = "RM_FAILURE"
    else:
        status = "EC_FAILURE"

    ##################### Measured durations for deployment, execution, and release
    # Get time deltas in miliseconds
    s2us = 1000000.0 # conversion factor s to microseconds = 10^6
    s2ms = 1000.0 # conversion factor s to microseconds = 10^3

    ## TTD: Time to deploy experiment
    ## Time between experiment deployment invoked and finished
    ttd = ttdf_time - ttd_time
    ttdms =  (ttd.microseconds + ((ttd.seconds + ttd.days * 24 * 3600) * s2us)) / s2ms

    ## TTR: Time to run experiment 
    ## Time between experiment deployment finished and experiment execution finished
    ttr = (ttef_time - ttdf_time)
    ttrms =  (ttr.microseconds + ((ttr.seconds + ttr.days * 24 * 3600) * s2us)) / s2ms

    ## TTREL: Time to release experiment
    ## Time between experiment shutdown invoked and finished
    ttrel = (ttsf_time - tts_time)
    ttrelms = (ttrel.microseconds + ((ttrel.seconds + ttrel.days * 24 * 3600) * s2us)) / s2ms

    ############### Compute resource usage

    cpu_count = psutil.NUM_CPUS
    vmem = psutil.virtual_memory()
    mem_total = vmem.total

    """
    n,m,std = compute_estimator(cpu_usage_deploy)
    cpu_deploy = "%d,%0.2f,%0.2f" % (n,m,std)

    n,m,std = compute_estimator(cpu_usage_execution)
    cpu_execution = "%d,%0.2f,%0.2f" % (n,m,std)

    n,m,std = compute_estimator(cpu_usage_release)
    cpu_release = "%d,%0.2f,%0.2f" % (n,m,std)

    n,m,std = compute_estimator(mem_usage_deploy)
    mem_deploy = "%d,%0.2f,%0.2f" % (n,m,std)

    n,m,std = compute_estimator(mem_usage_execution)
    mem_execution = "%d,%0.2f,%0.2f" % (n,m,std)

    n,m,std = compute_estimator(mem_usage_release)
    mem_release = "%d,%0.2f,%0.2f" % (n,m,std)
    """
    
    cpu_deploy = ",".join(map(str, cpu_usage_deploy))
    cpu_execution = ",".join(map(str, cpu_usage_execution))
    cpu_release = ",".join(map(str, cpu_usage_release))
    mem_deploy = ",".join(map(str, mem_usage_deploy))
    mem_execution = ",".join(map(str, mem_usage_execution))
    mem_release = ",".join(map(str, mem_usage_release))

    ############### Append results to file

    timestmp = ttd_time.strftime('%Y%m%d %H:%M:%S')
    osinfo = pltfrm.platform()
    ip = socket.gethostbyname(socket.gethostname())
    nepi_revision = get_nepi_revision()

    date = ttd_time.strftime('%Y%m%d')
    filename = "%s_scalability_benchmark_rev_%s_%s.data" % (platform, nepi_revision, date)
    filename = os.path.join(results, filename)

    if not os.path.exists(filename):
        f = open(filename, "w")
        f.write("timestamp|platform|node_count|app_count|thread_count|run#|"
            "delay(sec)|opdelay(sec)|cpu_count#|cpu_deploy(%)|cpu_execution(%)|"
            "cpu_release(%s)|mem_total(B)|mem_deploy(%)|mem_execution(%)|"
            "mem_release(%s)|TTD(ms)|TTR(ms)|TTREL(ms)|STATUS|IP|OS_info|NEPI_revision\n")
    else:
        f = open(filename, "a")

    f.write("%s|%s|%d|%d|%d|%d|%0.1f|%0.1f|%d|%s|%s|%s|%d|%s|%s|%s|%d|%d|%d|%s|%s|%s|%s\n" % (
        timestmp,
        platform,
        node_count,
        app_count,
        thread_count,
        run,
        delay, 
        opdelay,
        cpu_count,
        cpu_deploy,
        cpu_execution,
        cpu_release,
        mem_total,
        mem_deploy,
        mem_execution,
        mem_release,
        ttdms,
        ttrms,
        ttrelms,
        status,
        ip,
        osinfo,
        nepi_revision
      ))

    f.close()

if __name__ == '__main__':

    ## Get command-line arguments
    (node_count, app_count, thread_count, run, opdelay, delay, 
            platform, results) = parse_args()

    # Set the number of threads. 
    # NOTE: This must be done before instantiating the EC.
    os.environ["NEPI_NTHREADS"] = str(thread_count)

    ## Configure resources monitoring threads 
    cpu_usage_deploy = []
    cpu_usage_execution = []
    cpu_usage_release = []

    mem_usage_deploy = []
    mem_usage_execution = []
    mem_usage_release = []

    stop_monitor_deploy = []
    stop_monitor_execution = []
    stop_monitor_release = []

    thread_monitor_deploy = threading.Thread(target=monitor_resources, 
            args=(cpu_usage_deploy, mem_usage_deploy, stop_monitor_deploy))

    thread_monitor_execution = threading.Thread(target=monitor_resources, 
            args=(cpu_usage_execution, mem_usage_execution, stop_monitor_execution))

    thread_monitor_release = threading.Thread(target=monitor_resources, 
            args=(cpu_usage_release, mem_usage_release, stop_monitor_release))

    ## Load module
    mod = imp.load_source(platform, "%s.py" % platform)

    ## Construct the experiment description
    ec, apps, wait_rms = mod.make_experiment(node_count, app_count, 
            opdelay, delay)

    ## Time experiment deployment invoked
    ttd_time = datetime.datetime.now()

    ## Launch thread to monitor deploy CPU and memory usage
    thread_monitor_deploy.start()

    ## Deploy experiment
    ec.deploy()

    ## Wait until nodes and apps are deployed
    ec.wait_deployed(wait_rms)

    ## Time experiment deployment finished
    ttdf_time = datetime.datetime.now()

    ## Launch thread to monitor runtime CPU and memory usage
    thread_monitor_execution.start()

    ## Stop deploy monitoring thread
    stop_monitor_deploy.append(0)

    ## Wait until the apps are finished
    ec.wait_finished(apps)

    ## Time experiment execution finished
    ttef_time = datetime.datetime.now()

    ## Stop execution monitoring thread
    stop_monitor_execution.append(0)

    try:
        ## Validate experiment results
        mod.validate(ec, apps, wait_rms)
    except:
        import traceback
        import sys
        traceback.print_exc(file=sys.stdout)
        ec.fm.set_ec_failure()

    ## Time experiment shutdown invoked
    tts_time = datetime.datetime.now()

    ## Launch thread to monitor release CPU and memory usage
    thread_monitor_release.start()

    ## Perform experiment controller shutdown
    ec.shutdown()

    ## Time experiment shutdown finished
    ttsf_time = datetime.datetime.now()

    ## Stop release monitoring thread
    stop_monitor_release.append(0)

    ## Persist results
    persist_results(ec, platform, results, cpu_usage_deploy, cpu_usage_execution, 
        cpu_usage_release, mem_usage_deploy, mem_usage_execution, 
        mem_usage_release, ttd_time, ttdf_time, ttef_time, 
        tts_time, ttsf_time)

