# $1 — збірка, $2 — вихід. Повтор зі зіставленням за схожістю (replay_сцени.py), бо точний обмін рве на зміненому промпті.
cd /home/user/kod-shi-data
T=аудит/проби/автоживий-eebb37ae0aa73a0b429898cf7a6bca4daecfb462/ж6_побачення_вечір
rm -rf "$2"; mkdir -p "$2/знімки"
python3 аудит/проби/replay_сцени.py $T 0 > "$2/replay.txt" 2>&1 &
P=$!
for i in $(seq 1 60); do grep -q REPLAY_READY "$2/replay.txt" && break; sleep 1; done
URL=$(grep -o 'http://[0-9.:]*' "$2/replay.txt" | head -n 1)
python3 -c "import json;print(json.load(open('$T/повтор.json'))['жінка'].__repr__())" >/dev/null
python3 - "$T/повтор.json" "$2/жінка.json" <<'PY'
import json,sys;json.dump(json.load(open(sys.argv[1]))['жінка'],open(sys.argv[2],'w'),ensure_ascii=False)
PY
env FOTO=0 CHAT_TEXT="побачення в ресторані ввечері, о 19:30" MODEL=claude-sonnet-5-5 MODEL_MOVA=claude-sonnet-5-5 \
  SCENA=ж6_побачення_вечір OTSINKA=0 ZHINKA="$2/жінка.json" ZNIMKY="$2/знімки" MODEL_URL="$URL/v1" \
  CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=джерела/node_modules \
  timeout 900 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 "$1" /tmp/pyodide 3 > "$2/лог.txt" 2>&1
echo "rc $?"
kill $P
