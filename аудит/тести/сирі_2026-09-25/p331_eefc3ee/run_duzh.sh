#!/bin/sh
# вирівнювання дужок (PR після #329): 3 прогони на сід, через один сід; новий прогін не стартує після 18:18 UTC
# виклик: run_duzh.sh <тека збірки> <мітка-префікс>
ST="$1"; P="$2"
IR="гуляю з собаками в парку, вітер, яскраво хочу одягатись, по-дівчачому, ніжний і зручний образ у світлих тонах, у мене є світлі джинси кльош"
zav() { "/c/Users/Admin/.lmstudio/bin/lms.exe" ps | grep -q gemma-4-12b-it-qat || curl -s -m 600 -X POST http://127.0.0.1:1234/api/v1/models/load -H "Content-Type: application/json" -d '{"model":"gemma-4-12b-it-qat","context_length":61440,"flash_attention":true,"parallel":1}' > /dev/null; }
cd /c/tmp
for r in 13:1 7:1 13:2 7:2 13:3 7:3; do
  S=${r%%:*}; N=${r#*:}
  if [ "$(date -u +%H%M)" -ge 1818 ]; then echo "ЗУПИНЕНО на ${P}_ir_s${S}_$N: після 18:18 UTC новий прогін не стартує"; break; fi
  zav; STEND=$ST MODEL=gemma-4-12b-it-qat CHAT_TEXT="$IR" sh /c/tmp/p2/run_stend_x.sh ${P}_ir_s${S}_$N $S
done
"/c/Users/Admin/.lmstudio/bin/lms.exe" unload gemma-4-12b-it-qat > /dev/null 2>&1
echo "ГОТОВО duzh $(date -u +%H:%M)"
