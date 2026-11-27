#!/bin/bash
R=/home/user/kod-shi-data; OUT=/tmp/run
export CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules ZHYVA=sonnet PYODIDE=/tmp/pyodide
c7() { ( cd $R && env STOR=$1 SHLIAKH=ядро PROHODY=1 $3 timeout 1800 python3 аудит/звіти/ядро-образу-наново/приймання/пройти.py с7 $OUT/$2 > $OUT/$2.log 2>&1; echo "rc=$?" >> $OUT/$2.log ) }
rm -rf $OUT/с7-без-ДО-main* $OUT/с7-з-ДО-main*
c7 /tmp/stor-main с7-без-ДО-main N6_NO_PORTRAIT=1 &
c7 /tmp/stor-main с7-з-ДО-main &
wait
c7 /tmp/stor-h4854 с7-з-ПІСЛЯ-4854-рядок &
c7 /tmp/stor-h4854 с7-без-ПІСЛЯ-4854-рядок N6_NO_PORTRAIT=1 &
wait
echo ВСЕ
