#!/usr/bin/env python

###############################################################################
#
#    NEPI, a framework to manage network experiments
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
#
###############################################################################
from nepi.execution.ec import ExperimentController 
from nepi.execution.runner import ExperimentRunner
from nepi.util.netgraph import TopologyType
import nepi.data.processing.ccn.parser as ccn_parser

import networkx
import socket
import os
import numpy
from scipy import stats
from matplotlib import pyplot
import math
import random

def avg_interest_rtt(ec, run):
    logs_dir = ec.run_dir
    
    # Parse downloaded CCND logs
    (graph,
      content_names,
      interest_expiry_count,
      interest_dupnonce_count,
      interest_count,
      content_count) = ccn_parser.process_content_history_logs(
        logs_dir, ec.netgraph.topology)

    # statistics on RTT
    rtts = [content_names[content_name]["rtt"] \
            for content_name in content_names.keys()]

    # sample mean and standard deviation
    sample = numpy.array(rtts)
    n, min_max, mean, var, skew, kurt = stats.describe(sample)
    std = math.sqrt(var)
    ci = stats.t.interval(0.95, n-1, loc = mean, 
            scale = std/math.sqrt(n))

    global metrics
    metrics.append((mean, ci[0], ci[1]))
    
    return mean

def normal_law(ec, run, sample):
    x = numpy.array(sample)
    n = len(sample)
    std = x.std()
    se = std / math.sqrt(n)
    m = x.mean()
    se95 = se * 2
    
    return m * 0.05 >= se95

def post_process(ec, runs):
    global metrics
    
    # plot convergence graph
    y = numpy.array([float(m[0]) for m in metrics])
    low = numpy.array([float(m[1]) for m in metrics])
    high = numpy.array([float(m[2]) for m in metrics])
    error = [y - low, high - y]
    x = range(1,runs + 1)

    # plot average RTT and confidence interval for each iteration
    pyplot.errorbar(x, y, yerr = error, fmt='o')
    pyplot.plot(x, y, 'r-')
    pyplot.xlim([0.5, runs + 0.5])
    pyplot.xticks(numpy.arange(1, len(y)+1, 1))
    pyplot.xlabel('Iteration')
    pyplot.ylabel('Average RTT')
    pyplot.grid()
    pyplot.savefig("plot.png")
    pyplot.show()

content_name = "ccnx:/test/bunny.ts"

STOP_TIME = "5000s"

repofile = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 
        "repoFile1.0.8.2")

def get_simulator(ec):
    simulator = ec.filter_resources("linux::ns3::Simulation")

    if not simulator:
        node = ec.register_resource("linux::Node")
        ec.set(node, "hostname", "localhost")

        simu = ec.register_resource("linux::ns3::Simulation")
        ec.register_connection(simu, node)
        return simu

    return simulator[0]

def add_collector(ec, trace_name, subdir, newname = None):
    collector = ec.register_resource("Collector")
    ec.set(collector, "traceName", trace_name)
    ec.set(collector, "subDir", subdir)
    if newname:
        ec.set(collector, "rename", newname)

    return collector

def add_dce_host(ec, nid):
    simu = get_simulator(ec)
    
    host = ec.register_resource("ns3::Node")
    ec.set(host, "enableStack", True)
    ec.register_connection(host, simu)

    # Annotate the graph
    ec.netgraph.annotate_node(nid, "host", host)
    
def add_dce_ccnd(ec, nid):
    # Retrieve annotation from netgraph
    host = ec.netgraph.node_annotation(nid, "host")
    
    # Add dce ccnd to the dce node
    ccnd = ec.register_resource("linux::ns3::dce::CCND")
    ec.set (ccnd, "stackSize", 1<<20)
    ec.set (ccnd, "debug", 7)
    ec.set (ccnd, "capacity", 50000)
    ec.set (ccnd, "StartTime", "1s")
    ec.set (ccnd, "StopTime", STOP_TIME)
    ec.register_connection(ccnd, host)

    # Collector to retrieve ccnd log
    collector = add_collector(ec, "stderr", str(nid), "log")
    ec.register_connection(collector, ccnd)

    # Annotate the graph
    ec.netgraph.annotate_node(nid, "ccnd", ccnd)

def add_dce_ccnr(ec, nid):
    # Retrieve annotation from netgraph
    host = ec.netgraph.node_annotation(nid, "host")
    
    # Add a CCN content repository to the dce node
    ccnr = ec.register_resource("linux::ns3::dce::CCNR")
    ec.set (ccnr, "repoFile1", repofile) 
    ec.set (ccnr, "stackSize", 1<<20)
    ec.set (ccnr, "StartTime", "2s")
    ec.set (ccnr, "StopTime", STOP_TIME)
    ec.register_connection(ccnr, host)

def add_dce_ccncat(ec, nid):
    # Retrieve annotation from netgraph
    host = ec.netgraph.node_annotation(nid, "host")
   
    # Add a ccncat application to the dce host
    ccncat = ec.register_resource("linux::ns3::dce::CCNCat")
    ec.set (ccncat, "contentName", content_name)
    ec.set (ccncat, "stackSize", 1<<20)
    ec.set (ccncat, "StartTime", "8s")
    ec.set (ccncat, "StopTime", STOP_TIME)
    ec.register_connection(ccncat, host)

def add_dce_fib_entry(ec, nid1, nid2):
    # Retrieve annotations from netgraph
    host1 = ec.netgraph.node_annotation(nid1, "host")
    net = ec.netgraph.edge_net_annotation(nid1, nid2)
    ip2 = net[nid2]

    # Add FIB entry between peer hosts
    ccndc = ec.register_resource("linux::ns3::dce::FIBEntry")
    ec.set (ccndc, "protocol", "udp") 
    ec.set (ccndc, "uri", "ccnx:/") 
    ec.set (ccndc, "host", ip2)
    ec.set (ccndc, "stackSize", 1<<20)
    ec.set (ccndc, "StartTime", "2s")
    ec.set (ccndc, "StopTime", STOP_TIME)
    ec.register_connection(ccndc, host1)

def add_dce_net_iface(ec, nid1, nid2):
    # Retrieve annotations from netgraph
    host = ec.netgraph.node_annotation(nid1, "host")
    net = ec.netgraph.edge_net_annotation(nid1, nid2)
    ip1 = net[nid1]
    prefix = net["prefix"]

    dev = ec.register_resource("ns3::PointToPointNetDevice")
    ec.set(dev,"DataRate", "5Mbps")
    ec.set(dev, "ip", ip1)
    ec.set(dev, "prefix", prefix)
    ec.register_connection(host, dev)

    queue = ec.register_resource("ns3::DropTailQueue")
    ec.register_connection(dev, queue)

    return dev

def add_edge(ec, nid1, nid2):
    ### Add network interfaces to hosts
    p2p1 = add_dce_net_iface(ec, nid1, nid2)
    p2p2 = add_dce_net_iface(ec, nid2, nid1)

    # Create point to point link between interfaces
    chan = ec.register_resource("ns3::PointToPointChannel")
    ec.set(chan, "Delay", "0ms")

    ec.register_connection(chan, p2p1)
    ec.register_connection(chan, p2p2)

    #### Add routing between CCN nodes
    add_dce_fib_entry(ec, nid1, nid2)
    add_dce_fib_entry(ec, nid2, nid1)

def add_node(ec, nid):
    ### Add CCN nodes (ec.netgraph holds the topology graph)
    add_dce_host(ec, nid)
    add_dce_ccnd(ec, nid)
        
    if nid == ec.netgraph.targets()[0]:
        add_dce_ccnr(ec, nid)

    if nid == ec.netgraph.sources()[0]:
        add_dce_ccncat(ec, nid)

def wait_guids(ec):
    return ec.filter_resources("linux::ns3::dce::CCNCat")

if __name__ == '__main__':

    metrics = []

    # topology translation to NEPI model
    ec = ExperimentController("dce_4n_linear",
        topo_type = TopologyType.LINEAR, 
        node_count = 4,
        assign_st = True,
        assign_ips = True,
        add_node_callback = add_node,
	add_edge_callback = add_edge)

    #### Run experiment until metric convergence
    rnr = ExperimentRunner()
    runs = rnr.run(ec,
            min_runs = 10,
            max_runs = 100, 
            compute_metric_callback = avg_interest_rtt,
            evaluate_convergence_callback = normal_law,
            wait_guids = wait_guids(ec))
   
    ### post processing
    post_process(ec, runs)


