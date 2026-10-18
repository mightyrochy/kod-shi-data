#!/usr/bin/env bash
set -euo pipefail
source /workspace/liusterko-tools/activate.sh
export NODE_PATH=/workspace/work/f1-final/джерела/node_modules
export CHROMIUM=/usr/bin/chromium
F1OUT=/workspace/work/f1-results
F1SRC=/workspace/work/f1-final
for n in 1 2 3; do
 for side in pre42 final; do
  python3 - "$F1OUT/$side/assembly-$n-system.json" <<'PY'
from pathlib import Path
import json,sys,time
p=Path('/sys/fs/cgroup')
d={'unix':time.time(),'loadavg':Path('/proc/loadavg').read_text().strip(),'cpu_max':(p/'cpu.max').read_text().strip(),'cpu_stat':(p/'cpu.stat').read_text()}
Path(sys.argv[1]).write_text(json.dumps(d,indent=2)+'\n')
PY
  ZHYVA= FOTO=0 OTSINKA=0 CHASY=1 ZNIMKY="$F1OUT/$side/shots-$n" CHASY_OUT="$F1OUT/$side/assembly-$n.json" node "$F1SRC/аудит/проби/рв6_стенд.js" http://127.0.0.1:8765 "$F1OUT/$side" /workspace/work/pyodide 3 > "$F1OUT/$side/assembly-$n.log" 2>&1
 done
done
