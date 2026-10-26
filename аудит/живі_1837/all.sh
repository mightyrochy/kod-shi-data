#!/bin/bash
D=/c/tmp/z1837/аудит/живі_1837; T=/c/tmp/z1837_out
bash $D/run.sh $D/сцени_повні.txt /c/tmp/z1837_site_pi ПІСЛЯ_повні повний 1
echo PART1 >> $T/done.txt
bash $D/run.sh $D/сцени_повні.txt /c/tmp/z1837_site_do ДО_повні повний 1
echo PART2 >> $T/done.txt
bash $D/run.sh $D/сцени_година.txt /c/tmp/z1837_site_pi ПІСЛЯ_година розмова 3
echo PART3 >> $T/done.txt
bash $D/run.sh $D/сцени_година.txt /c/tmp/z1837_site_do ДО_година розмова 3
echo PART4 >> $T/done.txt
