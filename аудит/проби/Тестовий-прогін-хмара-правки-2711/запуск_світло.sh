#!/bin/bash
# Додатковий замір для питання 5: копія рв6_стенд.js з одним вставленим блоком (світло.patch) читає текст вузла `#ф-світло-портрета`
# і знімає вікно 390×844 на вузлі поради — основний стенд знімає лише `#кол-блок`, де поради нема. Запуск з кореня репозиторію: bash запуск_світло.sh <N>
cd "$(git rev-parse --show-toplevel)"; T=аудит/проби/Тестовий-прогін-хмара-правки-2711; d=$T/17009__світло_$1; mkdir -p $d/знімки $d/VIDPOVIDI
cp аудит/проби/рв6_стенд.js /tmp/рв6_оригінал.js; patch -s -o аудит/проби/рв6_стенд_світло.js аудит/проби/рв6_стенд.js $T/світло.patch
eval "$(python3 аудит/проби/записати_сцену.py --сцена 17009 --лише-змінні | python3 -c 'import json,sys
for k,v in json.load(sys.stdin).items():
  if k not in ("MODEL","MODEL_MOVA"): print("export %s=%r"%(k,v))')"
ZHYVA=sonnet VIDPOVIDI=$d/VIDPOVIDI ZNIMKY=$d/знімки ZVIT_OUT=$d/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
  node аудит/проби/рв6_стенд_світло.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > $d/лог.txt 2>&1; echo rc=$?
