import matplotlib
matplotlib.use('GTK') 
import matplotlib.pyplot as plt
import numpy as np
import os
import time

import subprocess

##### Parsing Argument to Plot #####
from optparse import OptionParser

usage = ("usage: %prog -p <type-of-plot> -d <type-of-packets> -f <folder-with-stats>")

parser = OptionParser(usage = usage)
parser.add_option("-p", "--plot", dest="plot",
        help="Type of Plot : vod_broad_cli | vod_broad_wlan | vod_broad_eth | broad_all | vod_all", type="string")
parser.add_option("-d", "--packet", dest="packet",
        help="Packet to use for the plot : frames | bytes", type="string")
parser.add_option("-f", "--folder", dest="folder",
        help="Folder with the statistics ", type="string")

(options, args) = parser.parse_args()
plot = options.plot
packet = options.packet
folder = options.folder

##### Initialize the data #####

overall_stats_broad = {}
overall_stats_vod = {}

for i in [1, 3, 5]:
    overall_stats_broad[i] = {}
    overall_stats_broad[i]['eth'] = []
    overall_stats_broad[i]['wlan'] = []
    overall_stats_broad[i]['cli'] = []

    overall_stats_vod[i] = {}
    overall_stats_vod[i]['eth'] = []
    overall_stats_vod[i]['wlan'] = []
    overall_stats_vod[i]['cli'] = []

all_broad_folders = os.listdir(folder + 'demo_openlab_traces/broadcast')
all_vod_folders = os.listdir(folder + 'demo_openlab_traces/vod')

data_broad_folders = list()
data_vod_folders = list()

# Loop to take only the wanted folder
for f in all_broad_folders :
    if f.startswith('s_'): 
        data_broad_folders.append(f)

for f in all_vod_folders :
    if f.startswith('s_'): 
        data_vod_folders.append(f)

##### For Broadcast #####

stats_broad_wlan = list()
stats_broad_eth = list()
stats_broad_cli = list()

# Write the wanted statistics into a file
for exp in data_broad_folders :
    broad_file = os.listdir(folder + 'demo_openlab_traces/broadcast/'+exp)
    for f in broad_file :
        dest = folder + "demo_openlab_traces/broadcast/" + exp + "/stats_" + f + ".txt"
        command = "tshark -r " + folder + "demo_openlab_traces/broadcast/" + exp + "/" + f + " -z io,phs > " + dest
        if f.startswith('capwificen_wlan'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_broad_wlan.append(dest)
        if f.startswith('capwificen_eth'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_broad_eth.append(dest)
        if f.startswith('capcli'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_broad_cli.append(dest)

# Numer of client that was used
def nb_client(s):
    elt = s.split('_')
    if elt[-2] == '1':
        return 1
    if elt[-2] == '3':
        return 3
    if elt[-2] == '5':
        return 5

# Return the value wanted
def get_broad_values(list_files, type_file):
    for s in list_files:
        nb = nb_client(s)
        o = open(s, 'r')
        for l in o:
            if 'udp' in l:
                row = l.split(':')
                f = row[1].split(' ')
                frame = int(f[0])
                byte = int(row[2])

                res = {}
                res['frames'] = frame
                res['bytes'] = byte
                if frame < 20 :
                    continue
                overall_stats_broad[nb][type_file].append(res)
        o.close() 

get_broad_values(stats_broad_wlan, 'wlan')
get_broad_values(stats_broad_eth, 'eth')
get_broad_values(stats_broad_cli, 'cli')

#print overall_stats_broad

##### For VOD #####

stats_vod_wlan = list()
stats_vod_eth = list()
stats_vod_cli = list()

# Write the wanted statistics into a file
for exp in data_vod_folders :
    vod_file = os.listdir(folder + 'demo_openlab_traces/vod/'+exp)
    for f in vod_file :
        dest = folder + "/demo_openlab_traces/vod/" + exp + "/stats_" + f + ".txt"
        command = "tshark -r " + folder + "demo_openlab_traces/vod/" + exp + "/" + f + " -z io,phs > " + dest
        if f.startswith('capwificen_wlan'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_vod_wlan.append(dest)
        if f.startswith('capwificen_eth'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_vod_eth.append(dest)
        if f.startswith('capcli'):
            p = subprocess.Popen(command , shell=True)
            p.wait()
            stats_vod_cli.append(dest)

# Return the value wanted
def get_vod_values(list_files, type_file):
    for s in list_files:
        nb = nb_client(s)
        o = open(s, 'r')
        for l in o:
            if 'udp' in l:
                row = l.split(':')
                f = row[1].split(' ')
                frame = int(f[0])
                byte = int(row[2])

                res = {}
                res['frames'] = frame
                res['bytes'] = byte
                if frame < 100 :
                    continue
                overall_stats_vod[nb][type_file].append(res)
        o.close() 

get_vod_values(stats_vod_wlan, 'wlan')
get_vod_values(stats_vod_eth, 'eth')
get_vod_values(stats_vod_cli, 'cli')

#print overall_stats_vod

##### For Plotting #####

if plot != "vod_all":
    means_broad_cli = list()
    std_broad_cli = list()

    means_broad_wlan = list()
    std_broad_wlan = list()

    means_broad_eth = list()
    std_broad_eth = list()

    for i in [1, 3, 5]:
        data_cli = list()
        for elt in overall_stats_broad[i]['cli']:
            data_cli.append(elt['frames'])
        samples = np.array(data_cli)

        m = samples.mean()
        std = np.std(data_cli)
        means_broad_cli.append(m)
        std_broad_cli.append(std)

        data_wlan = list()
        for elt in overall_stats_broad[i]['wlan']:
            data_wlan.append(elt['frames'])
        samples = np.array(data_wlan)

        m = samples.mean()
        std = np.std(data_wlan)
        means_broad_wlan.append(m)
        std_broad_wlan.append(std)
    
        data_eth = list()
        for elt in overall_stats_broad[i]['eth']:
            data_eth.append(elt['frames'])
        samples = np.array(data_eth)

        m = samples.mean()
        std = np.std(data_eth)
        means_broad_eth.append(m)
        std_broad_eth.append(std)

if plot != "broad_all":
    means_vod_cli = list()
    std_vod_cli = list()

    means_vod_wlan = list()
    std_vod_wlan = list()

    means_vod_eth = list()
    std_vod_eth = list()

    for i in [1, 3, 5]:
        data_cli = list()
        for elt in overall_stats_vod[i]['cli']:
            data_cli.append(elt['frames'])
        samples = np.array(data_cli)

        m = samples.mean()
        std = np.std(data_cli)
        means_vod_cli.append(m)
        std_vod_cli.append(std)

        data_wlan = list()
        for elt in overall_stats_vod[i]['wlan']:
            data_wlan.append(elt['frames'])
        samples = np.array(data_wlan)

        m = samples.mean()
        std = np.std(data_wlan)
        means_vod_wlan.append(m)
        std_vod_wlan.append(std)
    
        data_eth = list()
        for elt in overall_stats_vod[i]['eth']:
            data_eth.append(elt['frames'])
        samples = np.array(data_eth)

        m = samples.mean()
        std = np.std(data_eth)
        means_vod_eth.append(m)
        std_vod_eth.append(std)

### To plot ###
n_groups = 3

#Put the right numbers
if plot == "broad_all":
    means_bars1 = tuple(means_broad_cli)
    std_bars1 = tuple(std_broad_cli)

    means_bars2 = tuple(means_broad_wlan)
    std_bars2 = tuple(std_broad_wlan)

    means_bars3 = tuple(means_broad_eth)
    std_bars3 = tuple(std_broad_eth)

if plot == "vod_all":
    means_bars1 = tuple(means_vod_cli)
    std_bars1 = tuple(std_vod_cli)

    means_bars2 = tuple(means_vod_wlan)
    std_bars2 = tuple(std_vod_wlan)

    means_bars3 = tuple(means_vod_eth)
    std_bars3 = tuple(std_vod_eth)

if plot == "vod_broad_cli":
    means_bars1 = tuple(means_broad_cli)
    std_bars1 = tuple(std_broad_cli)

    means_bars2 = tuple(means_vod_cli)
    std_bars2 = tuple(std_vod_cli)

if plot == "vod_broad_wlan":
    means_bars1 = tuple(means_broad_wlan)
    std_bars1 = tuple(std_broad_wlan)

    means_bars2 = tuple(means_vod_wlan)
    std_bars2 = tuple(std_vod_wlan)

if plot == "vod_broad_eth":
    means_bars1 = tuple(means_broad_eth)
    std_bars1 = tuple(std_broad_eth)

    means_bars2 = tuple(means_vod_eth)
    std_bars2 = tuple(std_vod_eth)


fig, ax = plt.subplots()

index = np.arange(n_groups)
bar_width = 0.3

opacity = 0.4
error_config = {'ecolor': '0.3'}

if plot == "vod_all" or plot == "broad_all" :
    rects1 = plt.bar(index, means_bars1, bar_width,
                 alpha=opacity,
                 color='y',
                 yerr=std_bars1,
                 error_kw=error_config,
                 label='Client')

    rects2 = plt.bar(index + bar_width, means_bars2, bar_width,
                 alpha=opacity,
                 color='g',
                 yerr=std_bars2,
                 error_kw=error_config,
                 label='Wlan')

    rects3 = plt.bar(index + 2*bar_width, means_bars3, bar_width,
                 alpha=opacity,
                 color='r',
                 yerr=std_bars3,
                 error_kw=error_config,
                 label='Eth')

else :
    rects1 = plt.bar(index, means_bars1, bar_width,
                 alpha=opacity,
                 color='y',
                 yerr=std_bars1,
                 error_kw=error_config,
                 label='Broadcast')

    rects2 = plt.bar(index + bar_width, means_bars2, bar_width,
                 alpha=opacity,
                 color='g',
                 yerr=std_bars2,
                 error_kw=error_config,
                 label='VOD')    

plt.xlabel('Number of Client')

if packet == "frames" :
    plt.ylabel('Frames sent over UDP')
if packet == "bytes" :
    plt.ylabel('Bytes sent over UDP')

if plot == "broad_all":
    plt.title('Packet sent by number of client in broadcast mode')
if plot == "vod_all":
    plt.title('Packet sent by number of client in VOD mode')
if plot == "vod_broad_cli":
    plt.title('Packet received in average by client in broadcast and vod mode')
if plot == "vod_broad_wlan":
    plt.title('Packet sent in average to the clients in broadcast and vod mode')
if plot == "vod_broad_eth":
    plt.title('Packet received in average by the wifi center in broadcast and vod mode')

plt.xticks(index + bar_width, ('1', '3', '5'))
plt.legend()

#plt.tight_layout()
plt.show()

