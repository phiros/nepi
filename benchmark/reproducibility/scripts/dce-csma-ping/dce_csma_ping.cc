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
#include "ns3/dce-module.h"

#include <iostream>
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
// * clone DCE
//
// $ cd $HOME/repos
// $ hg clone http://code.nsnam.org/ns-3-dce
//
// * install ns-3
//
// $ cd $HOME/repos/ns-3-allinone/ns-3-dev
// $ hg up -r 67ee979a1807
// $ ./waf configure --enable-examples -d optimized --prefix=$HOME/repos/ns-3-dce/build
// $ ./waf build
// $ ./waf install
//
// * install DCE
//
// $ cd $HOME/repos/ns-3-dce
// $ ./waf configure --with-ns3=$HOME/repos/ns-3-dce/build  --enable-opt --prefix=$HOME/repos/ns-3-dce
// $ ./waf build
// $ ./waf install
//
// * Install PING in DCE
//
// $ cd repos/ns-3-dce
// $ wget http://www.skbuff.net/iputils/iputils-s20101006.tar.bz2
// $ tar xvjf iputils-s20101006.tar.bz2
// $ cd iputils-s20101006/
// $ vim Makefile (replace "CFLAGS=" with "CFLAGS+=")
// $ make CFLAGS=-fPIC LDFLAGS="-pie -rdynamic" ping
// $ cp ping ../build/bin/
//
// * Install DCE ping script
//
// $ cd ~/repos/nepi/bechmark/reproducibility
// $ cp -r dce-csma-ping $HOME/repos/ns-3-dce/myscripts/
// $ export DCE_PATH=$PATH:$HOME/repos/ns-3-dce/build/bin_dce
// $ export DCE_ROOT=$PATH:$HOME/repos/ns-3-dce/build
//
// * Run DCE script
//
//  cd repos/ns-3-dce
//  ./waf --run "dce_csma_ping --nodes=1 --apps=1"
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

  DceManagerHelper dceManager;
  dceManager.Install (nodes);

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
          Ipv4Address ip = interfaces.GetAddress (r);
          std::ostringstream ipos;
          ip.Print(ipos);
          std::string ipstr = ipos.str();
          
          DceApplicationHelper dce;
          dce.SetStackSize (1 << 20);
          dce.SetBinary ("ping");
          dce.ResetArguments ();
          dce.ResetEnvironment ();
          dce.AddArgument ("-c 20");
          dce.AddArgument ("-s 1000");
          dce.AddArgument (ipstr.c_str());
          
          ApplicationContainer apps;
          apps = dce.Install (nodes.Get (i));
          apps.Start (Seconds (1.0));
        }
    }

  Simulator::Run ();
  Simulator::Destroy ();
  return 0;
}
