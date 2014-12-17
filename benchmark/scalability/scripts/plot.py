import numpy as numpy
import matplotlib.pyplot as pyplot
from matplotlib.backends.backend_pdf import PdfPages

from optparse import OptionParser

def compute_estimator(samples):
    if len(samples) == 0:
        return 0,0,0

    x = numpy.array(samples)
    n = len(samples)
    std = x.std() 
    m = x.mean()

    return n, m, std

def add_sample_data(data, thread_count, rm_count, sample):
    n,m,std = compute_estimator(sample)

    if not thread_count in data:
        data[thread_count] = dict()

    if not rm_count in data[thread_count]:
        data[thread_count][rm_count] = list()

    data[thread_count][rm_count].append(m)

    return data
 
def add_scalar_data(data, thread_count, rm_count, scalar):
    if not thread_count in data:
        data[thread_count] = dict()

    if not rm_count in data[thread_count]:
        data[thread_count][rm_count] = list()

    data[thread_count][rm_count].append(scalar)

    return data
 
def read_data(data_file):
    data_cpu_d = dict()
    data_cpu_e = dict()
    data_cpu_r = dict()

    data_mem_d = dict()
    data_mem_e = dict()
    data_mem_r = dict()

    data_time = dict()

    f = open(data_file, "r")

    for l in f:
        if l.startswith("timestamp|"):
            continue

        rows = l.split("|")
        platform = rows[1]
        node_count = int(rows[2])
        app_count = int(rows[3])
        thread_count = int(rows[4])
        delay = float(rows[6])
        opdelay = float(rows[7])

        status = rows[19]
        
        if status.strip() != "OK":
            continue

        if platform != "dummy":
            opdelay = "Nan"
        else:
            opdelay = "%.2f" % opdelay
        
        # Compute number of rms (1 dev per node)
        rm_count = node_count * 2 + app_count * node_count 

        cpu_d = rows[9]
        if cpu_d:
            cpu_d = map(float, cpu_d.split(","))
            add_sample_data(data_cpu_d, thread_count, rm_count, cpu_d)

        cpu_e = rows[10]
        if cpu_e:
            cpu_e = map(float, cpu_e.split(","))
            add_sample_data(data_cpu_e, thread_count, rm_count, cpu_e)
        
        cpu_r = rows[11]
        if cpu_r:
            cpu_r = map(float, cpu_r.split(","))
            add_sample_data(data_cpu_r, thread_count, rm_count, cpu_r)

        mem_d = rows[13]
        if mem_d:
            mem_d = map(float, mem_d.split(","))
            add_sample_data(data_mem_d, thread_count, rm_count, mem_d)

        mem_e = rows[14]
        if mem_e:
            mem_e = map(float, mem_e.split(","))
            add_sample_data(data_mem_e, thread_count, rm_count, mem_e)
    
        
        mem_r = rows[15]
        if mem_r:
            mem_r = map(float, mem_r.split(",")) 
            add_sample_data(data_mem_r, thread_count, rm_count, mem_r)

        ttd = int(rows[16])
        ttr = int(rows[17])
        ttrel = int(rows[18])

        # Compute total duration of experiment in seconds
        duration = (ttd + ttr + ttrel) / (1000.0)

        add_scalar_data(data_time, thread_count, rm_count, duration)
        
    f.close()

    return (data_cpu_d, data_cpu_e, data_cpu_r, data_mem_d, data_mem_e, 
            data_mem_r, data_time, platform, delay, opdelay)

def save_figure(figure, platform, delay, opdelay, metric, stage):
    outputfile = "%s_d_%.2f_o_%s_%s_%s.pdf" % (
            platform, delay, opdelay, metric, stage)
    pp = PdfPages(outputfile)
    pp.savefig(figure)
    pp.close()

def plot_data(data, platform, delay, opdelay, metric, stage, unit):
    plts = dict()

    for thread_count in sorted(data.keys()):
        plts[thread_count] = [[], [], [], []]

        rm_info = data[thread_count]
        for rm_count in sorted(rm_info.keys()):
            sample = rm_info[rm_count]
            
            x = numpy.array(sample)
            n = len(sample)
            std = x.std()
            m = x.mean()
            ci2 = numpy.percentile(sample, [2.5, 97.5])
        
            plts[thread_count][0].append(rm_count)
            plts[thread_count][1].append(m)
            plts[thread_count][2].append(m - ci2[0])
            plts[thread_count][3].append(ci2[1] - m)

    colors = ['red', 'orange', 'green', 'blue']

    fig = pyplot.figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)

    i = 0
    for thread_count in sorted(plts.keys()):
        info = plts[thread_count]
        x = info[0]
        y = info[1]
        ye1 = info[2]
        ye2 = info[3]

        # plot
        ax.errorbar(x, y, yerr=[ye1, ye2], fmt='-o', 
                label="%d threads" % thread_count,
                color = colors[i])
        i+=1

    ax.grid(True)

    ax.set_xlabel("# Resources")
    #plt.gca().set_xscale('log')

    ylabel = "%s %s" % (metric, unit)
    ax.set_ylabel(ylabel)
    #plt.gca().set_yscale('log')

    ax.legend(loc='lower right', framealpha=0.5)

    title = "%s - %s usage during %s\n" \
            "Reschedule / Operation delay = %.2f / %s " %  (
                    platform, metric, stage, delay, opdelay)
    ax.set_title(title)

    #pyplot.show()

    save_figure(fig, platform, delay, opdelay, metric, stage)

usage = ("usage: %prog -f <data-file>")

parser = OptionParser(usage = usage)
parser.add_option("-f", "--data-file", dest="data_file",
        help="File containing data to plot", type="string")

(options, args) = parser.parse_args()
data_file = options.data_file

(data_cpu_d, data_cpu_e, data_cpu_r, data_mem_d, data_mem_e, 
        data_mem_r, data_time, platform, delay, opdelay) = read_data(data_file)

plot_data(data_cpu_d, platform, delay, opdelay, "CPU", "deploy", "(%)")
plot_data(data_cpu_e, platform, delay, opdelay, "CPU", "execute", "(%)")
plot_data(data_cpu_r, platform, delay, opdelay, "CPU", "release", "(%)")

plot_data(data_mem_d, platform, delay, opdelay, "Memory", "deploy", "(%)")
plot_data(data_mem_e, platform, delay, opdelay, "Memory", "execute", "(%)")
plot_data(data_mem_r, platform, delay, opdelay, "Memory", "release", "(%)")

plot_data(data_time, platform, delay, opdelay, "Time", "total", "(sec)")

