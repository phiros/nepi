#!/bin/bash
## Run instructions:
## cd ~/repos/nepi/src/benchmark/scalability
## bash run_benchmark.sh

PLATFORM="dummy"
NODES=(1 10 50 100) # Number of nodes to try
APPS=(1 10 50) # Number of applications to try
THREADS=(1 10 50 100) # Number of threads to try
RUNS=15 # Number of time to reproduce each combination case
DELAY="0" # Re-scheduling delay for tasks
OPDELAY="0" # Time each operation take to execute, i.e., job durarion. 
            # only for dummy platform)
DATE=`date +"%m%d%y"`
TEST=0

################ Get arguments
usage()
{
cat << EOF
usage: $0 options

This script runs the NEPI benckmark for a given platform.
 
OPTIONS:
   -h      Show this message
   -p      Platform. One of: dummy, ns3, dce, linux, omf6
   -r      Number of runs per each (nodes#, applications#, threads#) combinations
   -d      Operation reschedule delay for the NEPI scheduler
   -o      Operation execution delay (dummy platform only)
   -t      Test run
EOF
}

# Initialize OPTIND
OPTIND=1        

while getopts "hp:r:d:o:t" opt; do
    case "$opt" in
    h)  usage
        exit 0
        ;;
    p)  PLATFORM=$OPTARG
        ;;
    r)  RUNS=$OPTARG
        ;;
    d)  DELAY=$OPTARG
        ;;
    o)  OPDELAY=$OPTARG
        ;;
    t)  TEST=1
        ;;
    esac
done

################ Configure benchmark
if [ $TEST -eq 1 ]
then
    RUNS=2
    NODES=(2) 
    APPS=(10)
else 
    case "$PLATFORM" in
    "dummy")
        NODES=(1 10 100 1000) 
        APPS=(1 10 50) 
        ;;
    "ns3")
        NODES=(1 10 100 1000) 
        APPS=(1 10 50) 
        ;;
    "dce")
        NODES=(1 10 100 500)
        APPS=(1 10 50)
        ;;
    "linux")
        NODES=(1 10 50 98)
        APPS=(1 10 50) 
        ;;
    "omf6")
        NODES=(1 10 15)
        APPS=(1 10 50) 
        ;;
    *)
        print "Wrong platform type"
        exit 0
        ;;
    esac
fi

mkdir -p ../logs

################ RUN BENCHMARK

for n in "${NODES[@]}"; do
    for a in "${APPS[@]}"; do
        for t in "${THREADS[@]}"; do
            for i in $(seq 1 $RUNS); do
                echo "Number of nodes = $n. Number of apps = $a. Number of threads = $t. Run $i."
                echo "PYTHONPATH=$PYTHONPATH:../../../src NEPI_LOGLEVEL=debug python benchmark.py -n $n -a $a -t $t -r $i -d $DELAY -o $OPDELAY -R ../results -p $PLATFORM > ../logs/$PLATFORM.nodes$n.apps$a.threads$t.run$i.$DATE.out 2>&1"
                PYTHONPATH=$PYTHONPATH:../../../src NEPI_LOGLEVEL=debug python benchmark.py -n $n -a $a -t $t -r $i -d $DELAY -o $OPDELAY -R ../results -p $PLATFORM > ../logs/$PLATFORM.nodes$n.apps$a.threads$t.run$i.$DATE.out 2>&1
                if [ $? != 0 ]; then
                    echo "Problem with node $n app $a thread $t execution the $i time"
                fi
            done
        done
    done
done


