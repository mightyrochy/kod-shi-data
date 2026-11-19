w=$1; shift
cd /tmp/$w
mkdir -p /tmp/зн4_$w
env CHROMIUM=/opt/pw-browsers/chromium FOTO=1 RUKA1_ZNIMOK=/tmp/зн4_$w/рука1_до_кінця.png ZNIMKY=/tmp/зн4_$w "$@" \
  timeout 1500 node /tmp/обгортка/знімок_руки1.js /tmp/$w/аудит/проби/рв6_стенд.js http://127.0.0.1:8765 /tmp/стенд_$w /tmp/pyodide 3 > /tmp/стенд4_$w.log 2>&1
echo "$w стенд=$?"
