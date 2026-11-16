# прогін.sh — тестовий прогін у хмарі (ZHYVA=sonnet), ДО (main) і ПІСЛЯ (гілка) на тих самих сценах без фото
ROOT=/home/user/kod-shi-data; OUT=/tmp/тс/прогін
odna() { # <сцена> <ДО|ПІСЛЯ> <тека index.html>
  ROW=$(grep "^$1|" $ROOT/аудит/проби/живі_сцени.txt); W=$(echo "$ROW" | cut -d'|' -f2); TXT=$(echo "$ROW" | cut -d'|' -f3)
  D="$OUT/$1/$2"; mkdir -p "$D/знімки" "$D/VIDPOVIDI"; t0=$(date +%s)
  env ZHYVA=sonnet OTSINKA=0 FOTO=0 CHAT_TEXT="$TXT" ZHINKA="$ROOT/аудит/проби/жінки/$W.json" VIDPOVIDI="$D/VIDPOVIDI" \
    ZNIMKY="$D/знімки" ZVIT_OUT="$D/вердикти.txt" SCENA="$1" CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node-tools/node_modules \
    node $ROOT/аудит/проби/рв6_стенд.js http://127.0.0.1:8765 "$3" /tmp/pyodide 3 > "$D/лог.txt" 2>&1
  echo "$1 $2 rc=$? с=$(( $(date +%s) - t0 ))" >> $OUT/хід.txt
}
mkdir -p $OUT
for s in б1_концерт_стримано ж3_зима; do
  odna $s ДО /tmp/тс/стенд-до & odna $s ПІСЛЯ /tmp/тс/стенд-після & wait
done
echo кінець >> $OUT/хід.txt
