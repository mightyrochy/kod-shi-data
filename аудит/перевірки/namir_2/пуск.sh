#!/bin/bash
# НАМІР-2 (рядки 842, 905, 1435) — живий прогін ПІСЛЯ на ноутбуці, локальні моделі LM Studio (CLAUDE.md п.10, п.15).
# $1 = ж1|ж7 ; $2 = 1 — ще другий лист (ROZMOVA=R_svekrukha.json). Потрібні MODEL=<стилістка> і MODEL_MOVA=<мовна модель>;
# збірка /tmp/стенд і кеш /tmp/pyodide — як у шапці `аудит/проби/рв6_стенд.js`.
# Приклад: MODEL=gemma-4-12b-it-qat MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 bash аудит/перевірки/namir_2/пуск.sh ж1 1
W=$1; R=${2:-0}; D=/tmp/namir2/${W}_ювілей_свекрухи$([ "$R" = 1 ] && echo _розмова); mkdir -p "$D"
ROOT=$(cd "$(dirname "$0")/../../.." && pwd); cd "$ROOT"
export FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$ROOT/аудит/проби/жінки/$W.json \
  CHAT_TEXT="ну короче в суботу ми йдемо до свекрухи на ювілей там буде ресторан і вся родина я не хочу щоб вона знов щось сказала"
[ "$R" = 1 ] && export ROZMOVA=$ROOT/аудит/перевірки/namir_2/R_svekrukha.json
CHROMIUM=${CHROMIUM:-/opt/pw-browsers/chromium} NODE_PATH=${NODE_PATH:-/opt/node22/lib/node_modules} \
  node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд /tmp/pyodide 3 > "$D/лог.txt" 2>&1
echo "rc=$? $D"
cd джерела && python3 проби/намір2_пул_межа.py "$D/VIDPOVIDI"
