#!/bin/bash
# Прогін однієї ситуації «як людина» через СПРАВЖНІЙ міст на типовій моделі сторінки (наряд Живий-через-міст-до-злиття).
# Запуск з кореня репозиторію на голові PR:  bash аудит/проби/Живий-через-міст/прогін.sh <ситуація> [тека-результату]
# Ситуації — теки аудит/проби/живий-як-людина-3/ (с1…с8). Одна сцена ≈ 9 хв (2 проходи) — запускати на ПЕРЕДНЬОМУ плані, по одній.
# Потрібні: uv (CPython 3.12.1), node + playwright (NODE_PATH), мережа через проксі середовища (токен моста підставляє проксі).
set -e
КОР=$(git rev-parse --show-toplevel); cd "$КОР"
С=${1:?ситуація}; ТЕКА=${2:-аудит/проби/Живий-через-міст}
export STOR=${STOR:-/tmp/стенд} PYODIDE=${PYODIDE:-/tmp/pyodide} NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
[ -d "$PYODIDE" ] || { mkdir -p /tmp/pyodide-dl && curl -sSL -o /tmp/pyodide-dl/p.tar.bz2 https://github.com/pyodide/pyodide/releases/download/0.26.4/pyodide-core-0.26.4.tar.bz2 && tar xjf /tmp/pyodide-dl/p.tar.bz2 -C /tmp; }
if [ ! -f "$STOR/index.html" ] || [ "$(cat $STOR/голова.txt 2>/dev/null)" != "$(git rev-parse HEAD)" ]; then
  uv python install 3.12.1 >/dev/null 2>&1; P=$(uv python find 3.12.1)
  mkdir -p "$STOR"; (cd джерела && LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON=$P python3 build_артефакт.py . "$STOR/index.html" показ-повний) > "$STOR/збирання.txt" 2>&1
  git rev-parse HEAD > "$STOR/голова.txt"      # ~4 хв
fi
pgrep -f повтор_міст.js >/dev/null && { echo "повтор_міст.js уже йде — не запускаю другий (два процеси писали в одну теку)"; exit 1; }
node аудит/проби/Живий-через-міст/стенд/повтор_міст.js "$С" "$ТЕКА" 0
