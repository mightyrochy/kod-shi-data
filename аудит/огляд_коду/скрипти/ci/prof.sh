cd wt/джерела
export PYTHONHASHSEED=0
runs(){ n=$1; shift
  nice -n 10 python3 -X importtime "$@" > /dev/null 2> ../../logs/imp_$n.txt
  nice -n 10 python3 ../../prof.py $n "$@" 2>/dev/null; echo "$n done $(date +%T) load $(cut -d' ' -f1 /proc/loadavg)"; }
runl(){ n=$1; shift
  nice -n 10 python3 -X importtime ../../prof.py $n "$@" 2> ../../logs/imp_$n.txt; echo "$n done $(date +%T) load $(cut -d' ' -f1 /proc/loadavg)"; }
runs dym стенд_знімок.py --дим
runs protokol тест_протоколу.py
runs kontrakty audit_contracts.py
runl zhyvyi тест_живого_шляху.py
runl rozdily прилади/розділи_гейтів.py
