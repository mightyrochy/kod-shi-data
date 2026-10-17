#!/bin/bash
# usage: tm.sh name cmd...  (в джерела/) 
n=$1; shift
echo "uptime: $(uptime | sed 's/.*load/load/')" > ../../logs/$n.time
/usr/bin/time -v nice -n 10 "$@" > ../../logs/$n.out 2> ../../logs/$n.err; echo "rc=$?" >> ../../logs/$n.time
grep -E 'Elapsed|User time|System time|Maximum resident|Percent of CPU' ../../logs/$n.err | sed 's/^\s*//' >> ../../logs/$n.time
