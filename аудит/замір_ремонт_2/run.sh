#!/bin/bash
# ЗАМІР-РЕМОНТ-2: main 43f0d85b (#906) + інструмент #917 (8565bcdb); qwen/qwen3.5-9b ctx 81920 на :1234.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
R=/c/Users/Admin/zamir2; A=$R/аудит/замір_ремонт_2; DO=C:/tmp/zr2/р1/аудит/ремонт1_замір/після; L=/c/tmp/zr2/хід.txt
G=../аудит/проби/гг1_повтор_ремонту.py
push(){ cp $L $A/хід.txt; ( cd $R && git add аудит/замір_ремонт_2 && git commit -qm "замір-ремонт-2: $1

Co-Authored-By: Claude Code <noreply@anthropic.com>" ); for i in 1 2 3 4; do ( cd $R && git push --no-thin -q -u origin claude/zamir-remont-2 ) && break; sleep $((2<<i)); done; }
cd $R/джерела
for N in 14 28; do LYSHE=$N VYVID=$A/р2_після BOKY=з_гг1 python3 -c "import os,runpy;os.environ['ЗАМІНА_ПУЛУ']='0';runpy.run_path('$G',run_name='__main__')" >> $L 2>&1; echo "р2 $N rc=$? $(date +%T)" >> $L; push "р2_після $N"; done
python3 ../аудит/проби/ремонт2_повтор_записів.py $A/р2_після $A/р2_після.json >> $L 2>&1
( cd $R && python3 аудит/проби/ремонт1_до_після.py $DO $A/р2_після; python3 аудит/проби/ремонт2_повтор_записів.py --порівняти $DO аудит/ремонт2_замір/до.json $A/р2_після $A/р2_після.json ) > $A/р2_порівняння.txt 2>&1
push "р2 порівняння"
for N in 7 14 21 28; do LYSHE=$N VYVID=$A/гг1_пари python3 $G >> $L 2>&1; echo "гг1 $N rc=$? $(date +%T)" >> $L; push "гг1_пари $N"; done
date +%T > $A/ALLDONE; push ALLDONE
