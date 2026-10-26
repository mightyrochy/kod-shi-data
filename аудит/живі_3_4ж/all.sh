#!/bin/bash
D=/c/tmp/z34zh/аудит/живі_3_4ж; T=/c/tmp/z34zh_out; mkdir -p $T
bash $D/run.sh $D/сцени_1837.txt П7_1837 3
echo PART1 >> $T/done.txt
bash $D/run.sh $D/сцени_1825.txt П7_1825 1
echo ALLDONE >> $T/done.txt
