#!/bin/bash
# Прогін однієї ситуації «як людина» через СПРАВЖНІЙ міст на типовій моделі сторінки (наряд Живий-через-міст-до-злиття).
# Запуск з кореня репозиторію на голові PR:  bash аудит/проби/Живий-через-міст/прогін.sh <ситуація> [тека-результату]
# Ситуації — теки аудит/проби/живий-як-людина-3/ (с1…с8). Одна сцена ≈ 9 хв (2 проходи) — запускати на ПЕРЕДНЬОМУ плані, по одній.
# Потрібні: uv (CPython 3.12.1), node + playwright (NODE_PATH), мережа через проксі середовища (токен моста підставляє проксі).
# Для Н6: SHLIAKH=ядро|старий, перший аргумент «всі» або номери ситуацій через кому; PROHODY=1 для проби.
set -e
ROOT=$(git rev-parse --show-toplevel); cd "$ROOT"
SIT=${1:?ситуація}; OUT=${2:-аудит/проби/Живий-через-міст}
PRYIMANNIA=аудит/звіти/ядро-образу-наново/приймання/пройти.py
case ${SHLIAKH:-} in
  ядро|старий)
    if [ -n "${REPLAY_PLAN:-}" ]; then exec python3 "$PRYIMANNIA" "$SIT" "$OUT"; fi
    if [ -n "${ZHYVA:-}" ] && ! command -v "${ZHYVA_BIN:-/opt/node22/bin/claude}" >/dev/null; then
      echo 'Для прогону за підпискою потрібен виконуваний claude (ZHYVA_BIN).' >&2
      exit 2
    fi
    ;;
  '')
    SIT=${SIT##*/}
    for d in аудит/проби/живий-як-людина-3/"${SIT}"*/; do
      d=${d%/}
      [ -f "$d/хід.md" ] && { SIT=${d##*/}; break; }
    done
    [ -f "аудит/проби/живий-як-людина-3/$SIT/хід.md" ] || { echo "нема ситуації $SIT у аудит/проби/живий-як-людина-3/"; exit 2; }
    ;;
  *) echo 'SHLIAKH має бути «ядро» або «старий».' >&2; exit 2 ;;
esac
export STOR=${STOR:-/tmp/стенд} PYODIDE=${PYODIDE:-/tmp/pyodide} NODE_PATH=${NODE_PATH:-/opt/node-tools/node_modules}
[ -d "$PYODIDE" ] || { mkdir -p /tmp/pyodide-dl && curl -sSL -o /tmp/pyodide-dl/p.tar.bz2 https://github.com/pyodide/pyodide/releases/download/0.26.4/pyodide-core-0.26.4.tar.bz2 && tar xjf /tmp/pyodide-dl/p.tar.bz2 -C /tmp; }
if [ ! -f "$STOR/index.html" ] || [ "$(cat "$STOR/голова.txt" 2>/dev/null)" != "$(git rev-parse HEAD)" ]; then
  P=${LYUSTERKO_PYC_PYTHON:-}
  if [ -z "$P" ]; then
    uv python install 3.12.1 >/dev/null 2>&1
    P=$(uv python find 3.12.1)
  fi
  mkdir -p "$STOR"; (cd джерела && LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON=$P python3 build_артефакт.py . "$STOR/index.html" показ-повний) > "$STOR/збирання.txt" 2>&1
  git rev-parse HEAD > "$STOR/голова.txt"      # ~4 хв
fi
if [ -n "${SHLIAKH:-}" ]; then exec python3 "$PRYIMANNIA" "$SIT" "$OUT"; fi
pgrep -f chrome-headless-shell >/dev/null && { echo "прогін уже йде (chrome-headless-shell) — не запускаю другий (два процеси писали в одну теку)"; exit 1; }
node аудит/проби/Живий-через-міст/стенд/повтор_міст.js "$SIT" "$OUT" 0
