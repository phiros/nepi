/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/csma-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/ipv4-global-routing-helper.h"

#include <time.h>
#include <stdlib.h>

// Default Network Topology
//
//      
//     n1   n2   n3   n4
//      |    |    |    |
//      ================
//        LAN 10.0.0.0
//
// Instructions
//
// * clone ns-3
//
// $ cd $HOME/repos
// $ hg  clone http://code.nsnam.org/ns-3-allinone -r 2c860e2e968f
// $ cd ns-3-allinone
// $ ./download.py
//
// * install ns-3
//
// $ cd $HOME/repos/ns-3-allinone/ns-3-dev
// $ ./waf configure --enable-examples -d optimized 
// $ ./waf build
// $ ./waf install
//
// * Install ping script
//
// $ cd ~/repos/nepi/bechmark/reproducibility
// $ cp ns3_csma_ping $HOME/repos/ns-3-allinone/ns-3-dev/scratch
//
// * Run DCE script
//
// $ cd $HOME/repos/ns-3-allinone/ns-3-dev 
// $ ./waf --run "scratch/ns3_csma_ping --nodes=1 --apps=1"
//

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("PingBenchmark");


int 
main (int argc, char *argv[])
{
  uint32_t nnodes = 1;
  uint32_t napps = 1;

  CommandLine cmd;
  cmd.AddValue ("nodes", "Number of nodes", nnodes);
  cmd.AddValue ("apps", "Number of applications", napps);

  cmd.Parse (argc,argv);

  NodeContainer nodes;
  nodes.Create (nnodes);

  CsmaHelper csma;
  //csma.SetChannelAttribute ("DataRate", StringValue ("100Mbps"));
  csma.SetChannelAttribute ("Delay", TimeValue (Seconds (0)));

  NetDeviceContainer devices;
  devices = csma.Install (nodes);

  InternetStackHelper stack;
  stack.Install (nodes);

  Ipv4AddressHelper address;
  address.SetBase ("10.0.0.0", "255.255.255.0");
  Ipv4InterfaceContainer interfaces;
  interfaces = address.Assign (devices);

  srand(time(NULL));
 
  for (uint32_t i = 0; i < nnodes; i++)
    {
      for (uint32_t j = 0; j < napps; j++)
        {
          // Generating a random number between 0 and nnodes. 
          // This does not yield uniformly random interger within the range
          uint32_t r = rand() % nnodes;
          
          Ptr<V4Ping> app = CreateObject<V4Ping> ();
          app->SetAttribute ("Remote", Ipv4AddressValue (interfaces.GetAddress (r)));
          app->SetAttribute ("Verbose", BooleanValue (true));
          nodes.Get (i)->AddApplication (app);
          app->SetStartTime (Seconds (0.0));
          app->SetStopTime (Seconds (20.0));
        }
    }

  Simulator::Run ();
  Simulator::Destroy ();
  return 0;
}
