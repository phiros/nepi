#!/bin/bash
## Run instructions:
## cd /home/wlab18/Documents/Nepi/neco/nepi/src
## PYTHONPATH=$PYTHONPATH:/home/wlab18/Documents/Nepi/Code/nepi/src bash scalability/run_omf6_benchmark.sh

# SCALABILTY OMF6

run0=1
runn=10
nodes=(25) 
apps=(10 30 50)
threads=(10 50 100)
delay="0.5"

hosts=("J1" "I1" "E1" "H1" "F1" "D1" "G1" "K1" "K2" "D2" "E2" "E3" "L3" "D3" "K3" "D4" "K4" "E4" "D5" "E5"  "K6" "D6" "C6" "M18" "M20" "M22" )
#hosts=("K2" "E4" "C2" "M20" "E5")

mkdir -p logs

# Change number of nodes, apps, threads
for n in "${nodes[@]}"; do
    for a in "${apps[@]}"; do
        for t in "${threads[@]}"; do
            for i in $(seq $run0 $runn); do
                for h in "${hosts[@]}"; do
                    host="zotac"$h".wilab2.ilabt.iminds.be"
                    echo $host
                    ssh jtribino@$host "sudo killall ruby ; sudo service omf_rc start > /dev/null"
                done
                sleep 2
                echo "Number of nodes = $n. Number of apps = $a. Number of threads = $t. Run $i."
                echo "NEPI_LOGLEVEL=info python scalability/omf6.py -n $n -a $a -t $t -d $delay -r $i > logs/scheddelay$delay.nodes$n.apps$a.threads$t.runs$i.out 2>&1"
                NEPI_LOGLEVEL=info python scalability/omf6.py -n $n -a $a -t $t -d $delay -r $i > logs/omf6.scheddelay$delay.nodes$n.apps$a.threads$t.runs$i.out 2>&1
                if [ $? != 0 ]; then
                    echo "Problem with node $n app $a thread $t execution the $i time"
                fi
            done
        done
    done
done






