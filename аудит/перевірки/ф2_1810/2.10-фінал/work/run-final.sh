#!/usr/bin/env bash
set -euo pipefail
source /workspace/liusterko-tools/activate.sh
export PYTHONHASHSEED=0
F210ROOT=/workspace/work/f2-210
F210OUT="$F210ROOT/work/final-after"
F210INPUT=/workspace/work/baseline02/аудит/проби/знімок_входи_сід3.jsonl.gz
mkdir -p "$F210OUT"
cd "$F210ROOT"
test "$(git rev-parse HEAD)" = ea01edda004e181710b9f686a7203b1a2a31d227
git diff --exit-code HEAD -- джерела
git rev-parse HEAD > "$F210OUT/source-head.txt"
test "$(git hash-object каталог_повний.xml.gz)" = d0b87c9ccb0e9c3d4df05f0404b8f68cb84d6210
test "$(git hash-object "$F210INPUT")" = 340a7e9ea892d90dc3138b10793c2c1207370f8a
cd джерела
LYUSTERKO_CATALOG=повний python3 build_артефакт.py . "$F210OUT/index.html" показ-повний > "$F210OUT/build.log" 2>&1
# Штатний builder без локального node_modules пропускає jsdom; один цільовий тест готовими залежностями.
node тест_показу.js > "$F210OUT/jsdom.log" 2>&1
cd "$F210ROOT"
python3 джерела/прилади/знімок_мосту.py pyodide --сторінка "$F210OUT/index.html" --входи "$F210INPUT" --вихід "$F210OUT/snapshot.jsonl" --pyodide /workspace/work/pyodide > "$F210OUT/snapshot.log" 2>&1
set +e
python3 джерела/прилади/знімок_мосту.py --діф /workspace/work/baseline-results/main-1.jsonl "$F210OUT/snapshot.jsonl" > "$F210OUT/diff.log" 2>&1
F210DIFF=$?
set -e
printf '%s\n' "$F210DIFF" > "$F210OUT/diff.rc"
sha256sum "$F210OUT/index.html" "$F210OUT/snapshot.jsonl" > "$F210OUT/sha256.txt"
