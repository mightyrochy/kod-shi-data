#!/bin/bash
set -eu

ROOT=$(git rev-parse --show-toplevel)
BASE=e862f9ba896bec33ef9cb32ed934f7f8b98d378d
STAND_REF=f973d965a0b4a3b52079ad3ddb481bb9eb81a842
HEAD_REF=$(git rev-parse "${1:?Передай точний SHA голови #4848}^{commit}")
OUT=${2:-$(mktemp -d)}
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)

підготувати_стенд() {
  git -C "$ROOT" show "$STAND_REF:аудит/проби/рв6_стенд.js" > "$OUT/рв6_основа.js"
  patch -f -F 0 -o "$2" "$OUT/рв6_основа.js" < "$1"
  sed -i.bak 's/опис: x\.опис, опис_без_фото:/опис: x.опис, як_носити: x.як_носити, опис_без_фото:/' "$2"
  node --check "$2"
}

if [ "${STAND_ONLY:-0}" = 1 ]; then
  підготувати_стенд "$ROOT/аудит/проби/приймання-н2-782c/стенд/рв6_н2.patch" "$OUT/рв6_крок4.js"
  printf '%s\n' "$OUT/рв6_крок4.js"
  exit 0
fi

if [ -z "${ZHYVA_BIN:-}" ]; then ZHYVA_BIN=$(command -v claude || printf '%s' /opt/node22/bin/claude); fi
export ZHYVA_BIN
if [ ! -x "$ZHYVA_BIN" ]; then
  printf '%s\n' 'Потрібна виконувана Claude CLI із підпискою Sonnet.' >&2
  exit 1
fi

npm ci --prefix "$ROOT/джерела" --ignore-scripts --no-audit --no-fund
export NODE_PATH="$ROOT/джерела/node_modules"
if [ -z "${CHROMIUM:-}" ]; then "$ROOT/джерела/node_modules/.bin/playwright" install chromium; fi
sh "$ROOT/аудит/проби/стенд_pyodide_кеш.sh" "$OUT/pyodide"

for SIDE in до після; do
  REF=$HEAD_REF
  if [ "$SIDE" = до ]; then REF=$BASE; fi
  git -C "$ROOT" worktree add --detach "$OUT/код-$SIDE" "$REF"
  (
    cd "$OUT/код-$SIDE"
    STAND=аудит/проби/рв6_крок4.js
    підготувати_стенд аудит/проби/приймання-н2-782c/стенд/рв6_н2.patch "$STAND"
    if [ "$SIDE" = до ]; then
      # ДО зберігає попередню поведінку. У звіт додаються лише лічильники відхилень.
      python3 - <<'PY'
from pathlib import Path

path = Path("джерела/ядро/руки.py")
text = path.read_text(encoding="utf-8")
before = '    збій = Збій("текст_картки", "розбір", "facts", причина(результат.розбіжності), спроба=спроба)'
after = '''    лічба = dict(Counter(з["чому"] for з in результат.розбіжності))
    збій = Збій("текст_картки", "розбір", "facts", причина(результат.розбіжності), спроба=спроба,
               дані={"відхилення": лічба})'''
if text.count(before) != 1:
    raise SystemExit("Несумісна база повтору")
path.write_text(text.replace(before, after), encoding="utf-8")
PY
    fi
    mkdir -p "$OUT/стенд-$SIDE"
    (cd джерела && LYUSTERKO_CATALOG=повний python3 build_артефакт.py . "$OUT/стенд-$SIDE/index.html" показ-повний)
    while IFS='|' read -r SCENA ZH CHAT; do
      for SID in 3 4; do
        RUN="$OUT/$SIDE/$SCENA-$SID"
        mkdir -p "$RUN/знімки"
        if ! ZHYVA=sonnet MIST_WORKER=1 YADRO=1 OTSINKA=0 FOTO=1 \
          ZHINKA="$PWD/аудит/проби/приймання-н2-782c/стенд/жінки/$ZH" CHAT_TEXT="$CHAT" \
          N2_DUMP="$RUN/обміни.jsonl" N2_VHID="$RUN/вхід-v1.json" N2_STAN="$RUN/стан.json" \
          ZNIMKY="$RUN/знімки" ZVIT_OUT="$RUN/вердикти.txt" \
          node "$STAND" http://127.0.0.1:8765 "$OUT/стенд-$SIDE" "$OUT/pyodide" "$SID" > "$RUN/лог.txt" 2>&1; then
          printf '%s\n' "Збій $SIDE $SCENA сід $SID, журнал $RUN/лог.txt" >&2
        fi
      done
    done <<'СЦЕНИ'
с3|с3_оксана.json|на роботу пішки, увесь день дощ, взуття — замшеві чоботи
с5|с5_оксана.json|я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан
с8|с8_юлія.json|на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин
СЦЕНИ
  )
done

python3 "$OUT/код-після/аудит/проби/шар-текстів-крок4/мірило.py" "$OUT" | tee "$OUT/мірило.json"
printf '%s\n' "$OUT"
