#!/bin/bash
# ПЕРЕВІРКА-ПАЧКА-4 — живий ДО/ПІСЛЯ на ноутбуці (LM Studio; CLAUDE.md п.10, п.15).
# Використання: MODEL=<стилістка> MODEL_MOVA=<мовна модель> bash аудит/перевірки/pachka_4/сцени.sh <сцена> <ДО|ПІСЛЯ>
#   ДО    — гілка claude/pachka-1008-3, ПІСЛЯ — claude/pachka-1008-4 (PR #654); обидві збираються у свій worktree.
# Сцени (лише сценарії правок, ≤ 6): ж1 і ж7 — картки жінок у `аудит/проби/жінки/`.
#   1 · #651 неявний намір, ж1 (свекруха, «щоб без претензій»)      — перший лист + друга репліка ROZMOVA
#   2 · #651 той самий ювілей БЕЗ намірених слів, ж1                — контроль: intent_source=default, доза «на межі»
#   3 · #651 «щоб до мене не було жодних питань», ж7 (директор)     — неявний намір на корпоративі
#   4 · #652 «Оціни мій образ» (сцена 6 стенда, два фото)            — мова оцінки: без «шкала/ошатність 1–10», без биття знаків
#   5 · #652 у чаті про ошатність: «наскільки там має бути ошатно?»  — шкала ошатності не витікає в чат (рядок 1434-чат)
#   6 · #653 церква: «Де» картки — слова, не ключ `церква_служба`    — DO=rozmova, знімок картки сценарію
# Знімки й вердикти — /tmp/pachka4/<ДО|ПІСЛЯ>_<сцена>/ ; порівняти картки.txt, вердикти.txt і знімки очима.
S=${1:?сцена 1-6}; V=${2:?ДО|ПІСЛЯ}
BR=claude/pachka-1008-3; [ "$V" = "ПІСЛЯ" ] && BR=claude/pachka-1008-4
ROOT=$(cd "$(dirname "$0")/../../.." && pwd); cd "$ROOT"
WT=/tmp/pachka4/wt_$V; [ -d "$WT" ] || { git fetch -q origin "$BR" && git worktree add -q --detach "$WT" "origin/$BR"; }
mkdir -p /tmp/стенд_$V && (cd "$WT/джерела" && LYUSTERKO_CATALOG=повний python3 build_артефакт.py . /tmp/стенд_$V/index.html показ-повний >/dev/null)
D=/tmp/pachka4/${V}_$S; mkdir -p "$D"
export FOTO=1 ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI OTSINKA=0
case $S in
  1) export ZHINKA=$ROOT/аудит/проби/жінки/ж1.json ROZMOVA=$ROOT/аудит/перевірки/namir_2/R_svekrukha.json
     export CHAT_TEXT="ну короче в суботу ми йдемо до свекрухи на ювілей там буде ресторан і вся родина я не хочу щоб вона знов щось сказала";;
  2) export ZHINKA=$ROOT/аудит/проби/жінки/ж1.json CHAT_TEXT="в суботу йдемо до свекрухи на ювілей, ресторан, буде вся родина";;
  3) export ZHINKA=$ROOT/аудит/проби/жінки/ж7.json CHAT_TEXT="корпоратив, буде директор, хочу щоб до мене не було жодних питань";;
  4) export ZHINKA=$ROOT/аудит/проби/жінки/ж1.json; unset OTSINKA CHAT_TEXT;;
  5) export ZHINKA=$ROOT/аудит/проби/жінки/ж1.json DO=rozmova CHAT_TEXT="наскільки ошатно має бути в ресторан на день народження подруги, за шкалою?";;
  6) export ZHINKA=$ROOT/аудит/проби/жінки/ж1.json DO=rozmova CHAT_TEXT="в неділю йду до церкви на службу, потім обід у батьків";;
esac
CHROMIUM=${CHROMIUM:-/opt/pw-browsers/chromium} NODE_PATH=${NODE_PATH:-/opt/node22/lib/node_modules} \
  node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд_$V /tmp/pyodide 3 > "$D/лог.txt" 2>&1
echo "rc=$? $D"
