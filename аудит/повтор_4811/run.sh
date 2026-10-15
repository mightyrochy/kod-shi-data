#!/bin/bash
# ПОВТОР-4811: main 7019e75d; qwen/qwen3.5-9b ctx 81920 на :1234; ЗАМІНА_ПУЛУ=0.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
R=/c/tmp/p4811/W; A=/c/tmp/p4811/W/аудит/повтор_4811; D=/c/tmp/p4811/DO/аудит/живі_1510_А
G=../аудит/проби/гг1_повтор_ремонту.py
push(){ ( cd $R && git add аудит/повтор_4811 && git commit -qm "$1

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" ); for i in 1 2 3 4; do ( cd $R && git push --no-thin -q -u origin claude/povtor-4811 ) && break; sleep $((2<<i)); done; }
cd $R/джерела
for N in 7 14 21 28; do
  LYSHE=$N VYVID=$A/гг1_пари BOKY=з_гг1,без_гг1 MODEL_URL=http://127.0.0.1:1234/v1 MODEL=qwen/qwen3.5-9b python3 -c "import os,runpy;os.environ['ЗАМІНА_ПУЛУ']='0';runpy.run_path('$G',run_name='__main__')" >> $A/хід.txt 2>&1
  echo "ч$N rc=$? $(date +%T)" >> $A/хід.txt
  push "повтор-4811: $N з 28"
done
python3 ../аудит/проби/ремонт2_повтор_записів.py $A/гг1_пари $A/р2.json >> $A/хід.txt 2>&1
cd $R
python3 аудит/проби/ремонт1_до_після.py $D/ремонт_28 $A/гг1_пари > $A/порівняння.txt 2>&1
python3 аудит/проби/ремонт2_повтор_записів.py --порівняти $D/ремонт_28 $D/ремонт_28.json $A/гг1_пари $A/р2.json >> $A/порівняння.txt 2>&1
python3 -c "import gzip,json,glob,sys;R=[json.load(gzip.open(f,'rt',encoding='utf-8')) for f in glob.glob(sys.argv[1]+'/сирі/*.json.gz')];[print(b,'пар',sum(1 for z in R if z.get(b) and not z[b].get('збій')),'образів після',sum(len(z[b].get('образи_після') or []) for z in R if z.get(b)),'з блокером',sum(bool(о.get('блокує')) for z in R if z.get(b) for о in z[b].get('образи_після') or [])) for b in ('з_гг1','без_гг1')]" $A/гг1_пари > $A/боки.txt 2>&1
push "повтор-4811: підсумки"
date +%T > $A/ALLDONE; push "повтор-4811: ALLDONE"
