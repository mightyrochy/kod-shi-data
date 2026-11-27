#!/bin/bash
# run.sh — проходи перевірки 2711: розмова (#4896) і с7 (#4854), по два одночасно
R=/home/user/kod-shi-data; OUT=/tmp/run; mkdir -p $OUT
export CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules ZHYVA=sonnet PYODIDE=/tmp/pyodide
rozmova() { # <stor> <name>
  d=$OUT/$2; mkdir -p $d/знімки $d/VIDPOVIDI
  eval "$(cd $R && python3 аудит/проби/записати_сцену.py --сцена ж1_репліка_синя_сукня --режим 'розмова +фото «З чим вдягти цю сукню?»' --лише-змінні | python3 -c 'import json,sys,shlex; [print("export %s=%s"%(k,shlex.quote(v))) for k,v in json.load(sys.stdin).items() if k not in ("MODEL","MODEL_MOVA")]')"
  ( cd $R && VIDPOVIDI=$d/VIDPOVIDI ZNIMKY=$d/знімки ZVIT_OUT=$d/вердикти.txt timeout 1800 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $1 /tmp/pyodide 3 > $d/лог.txt 2>&1; echo "rc=$?" > $d/rc.txt )
}
c7() { # <stor> <name> [noportrait]
  ( cd $R && STOR=$1 SHLIAKH=ядро PROHODY=1 ${3:+N6_NO_PORTRAIT=1} timeout 1800 python3 аудит/звіти/ядро-образу-наново/приймання/пройти.py с7 $OUT/$2 > $OUT/$2.log 2>&1; echo "rc=$?" >> $OUT/$2.log )
}
rozmova /tmp/stor-main розмова-ДО-main & rozmova /tmp/stor-h4896 розмова-ПІСЛЯ-4896 & wait
c7 /tmp/stor-h4854 с7-без-ПІСЛЯ-4854 1 & c7 /tmp/stor-main с7-без-ДО-main 1 & wait
c7 /tmp/stor-h4854 с7-з-ПІСЛЯ-4854 & wait
echo ВСЕ
