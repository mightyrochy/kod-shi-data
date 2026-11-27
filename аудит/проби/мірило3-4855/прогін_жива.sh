#!/bin/bash
# Живий Sonnet (ZHYVA, `claude -p` стенда) на сторінці з латкою виміру й пулом 43400 (/tmp/стенд/index.html). З кореня: bash <цей> <тека виходу> [сцена]
OUT=$(realpath -m "${1:?тека виходу}"); ID=${2:-ж1_весілля_гостя}; mkdir -p "$OUT/знімки" "$OUT/VIDPOVIDI"
eval "$(python3 аудит/проби/записати_сцену.py --сцена $ID --лише-змінні --режим повне | python3 -c "import json,sys;[print('export %s=%s'%(k,__import__('shlex').quote(v)))for k,v in json.load(sys.stdin).items()if k not in('MODEL','MODEL_MOVA')]")"
ZHYVA=sonnet VYMIR_OUT="$OUT/вимір_меж.jsonl" VIDPOVIDI="$OUT/VIDPOVIDI" ZNIMKY="$OUT/знімки" ZVIT_OUT="$OUT/вердикти.txt" \
CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
 node аудит/проби/рв6_стенд_вимір.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > "$OUT/лог.txt" 2>&1; echo rc=$? >> "$OUT/лог.txt"
