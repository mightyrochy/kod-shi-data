#!/bin/bash
D=/c/tmp/z1837/аудит/живі_1837; T=/c/tmp/z1837_out
while ! grep -q PART4 $T/done.txt; do sleep 20; done
grep 'ж2_похорон' $D/сцени_повні.txt > $D/сцени_похорон.txt
bash $D/run.sh $D/сцени_похорон.txt /c/tmp/z1837_site_pi ПІСЛЯ_повтор повний 1
bash $D/run.sh $D/сцени_повтор.txt /c/tmp/z1837_site_pi ПІСЛЯ_повтор повний 1
bash $D/run.sh $D/сцени_повтор.txt /c/tmp/z1837_site_do ДО_повтор повний 1
echo PART5 >> $T/done.txt
