#!/bin/bash
## Run instructions:
## cd ~/repos/nepi/src/benchmark/scalability
## bash run_ns3_benchmark.sh


## SCALABILTY 
#### NS3

run0=2
runn=2
nodes=(1 2) 
apps=(1 2) 
threads=(1 2)  
#run0=1
#runn=10
#nodes=(1 10 100 1000) 
#apps=(1 10 50) 
#threads=(1 10 50 100)  
delay="0.5"
opdelay="0"

mkdir -p ../logs

# Change number of nodes [1, 10, 30, 100, 500] (apps = 1, threads = 20)
for n in "${nodes[@]}"; do
    for a in "${apps[@]}"; do
        for t in "${threads[@]}"; do
            for i in $(seq $run0 $runn); do
                echo "Number of nodes = $n. Number of apps = $a. Number of threads = $t. Run $i."
                echo "PYTHONPATH=$PYTHONPATH:../../../src NEPI_LOGLEVEL=debug python ../scripts/ns3.py -n $n -a $a -t $t -r $i -d $delay -o $opdelay -R ../results > ../logs/ns3.nodes$n.apps$a.threads$t.runs$i.out 2>&1"
                PYTHONPATH=$PYTHONPATH:../../../src NEPI_LOGLEVEL=debug python ../scripts/ns3.py -n $n -a $a -t $t -r $i -d $delay -o $opdelay -R ../results > ../logs/ns3.nodes$n.apps$a.threads$t.runs$i.out 2>&1
                if [ $? != 0 ]; then
                    echo "Problem with node $n app $a thread $t execution the $i time"
                fi
            done
        done
    done
done


