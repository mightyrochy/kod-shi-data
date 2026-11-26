#!/bin/bash
# run.sh <сторінка: до|після> <мітка> <FOTO 1|0> <текст>
R=$1; M=$2; F=$3; T=$4
PAGE=/tmp/ш1/$R; O=/tmp/ш1/out/$M; rm -rf $O; mkdir -p $O
export FOTO=$F NODE_PATH=/opt/node-tools/node_modules
cd /home/user/kod-shi-data
timeout 1500 node /tmp/ш1/стенд/rozmova.cjs $PAGE /tmp/pyodide $O $M "$T" > $O/лог.txt 2>&1; echo "rc=$?" >> $O/лог.txt
tail -n 3 $O/лог.txt
