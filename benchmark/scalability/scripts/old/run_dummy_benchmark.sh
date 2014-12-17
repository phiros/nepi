#!/bin/bash
## Run instructions:
## cd ~/repos/nepi/src/benchmark
## PYTHONPATH=$PYTHONPATH:~/repos/nepi/src/ bash scalability/run_dummy_benchmark.sh


## SCALABILTY 
#### DUMMY

run0=1
runn=10
nodes=(1 10 100 1000) 
apps=(1 10 50) 
threads=(1 10 50 100)  
delay="0.5"
opdelay="0"

mkdir -p logs

# Change number of nodes, apps, threads
for n in "${nodes[@]}"; do
    for a in "${apps[@]}"; do
        for t in "${threads[@]}"; do
            for i in $(seq $run0 $runn); do
                echo "Number of nodes = $n. Number of apps = $a. Number of threads = $t. Run $i."
                echo "NEPI_LOGLEVEL=debug python scalability/dummy.py -n $n -a $a -t $t -d $delay -o $opdelay -r $i > logs/scheddelay$delay.opdelay$opdelay.nodes$n.apps$a.threads$t.runs$i.out 2>&1"
                NEPI_LOGLEVEL=debug python scalability/dummy.py -n $n -a $a -t $t -d $delay -o $opdelay -r $i > logs/scheddelay$delay.opdelay$opdelay.nodes$n.apps$a.threads$t.runs$i.out 2>&1
                if [ $? != 0 ]; then
                    echo "Problem with node $n app $a thread $t execution the $i time"
                fi
            done
        done
    done
done

