#!/bin/bash
set -uo pipefail
source /workspace/liusterko-tools/activate.sh
export TMPDIR=/workspace/scratch/tmp/pachka1310-5/runtime-tmp
cd /workspace/scratch/tmp/pachka1310-5/repo/джерела
out=/workspace/scratch/tmp/pachka1310-5/evidence
mkdir -p "$out"
git rev-parse HEAD > "$out/battery-head.txt"
: > "$out/battery-status.tsv"
run(){ local label="$1"; shift; "$@" > "$out/battery-$label.log" 2>&1; local result=$?; printf '%s\t%s\n' "$label" "$result" >> "$out/battery-status.tsv"; }
run prepare python3 -c "import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"
run syntax python3 -c "import pathlib,subprocess,sys,py_compile; paths=list(pathlib.Path('.').rglob('*')); py=[p for p in paths if p.suffix=='.py' and 'node_modules' not in p.parts]; js=[p for p in paths if p.suffix=='.js' and 'node_modules' not in p.parts]; [py_compile.compile(str(p),doraise=True) for p in py]; checks=[subprocess.run(['node','--check',str(p)]).returncode for p in js]; print('Python',len(py),'JavaScript',len(js),'fails',sum(checks)); sys.exit(bool(sum(checks)))"
run split bash -c 'failed=0; for f in проби/поділ_*_ast.py; do python3 "$f" || failed=$((failed+1)); done; echo "ВПАЛО $failed"; test "$failed" -eq 0'
run smoke python3 стенд_знімок.py --дим
run path python3 тест_живого_шляху.py
run protocol python3 тест_протоколу.py
run gates python3 прилади/розділи_гейтів.py
run contracts python3 audit_contracts.py
run display node тест_показу.js
run bridge node тест_мосту.js
run reach python3 досяжність.py
python3 - "$out" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); print((p/'battery-status.tsv').read_text()); statuses=[l.split('\t')[1] for l in (p/'battery-status.tsv').read_text().splitlines()]; report=(p/'battery-reach.log').read_text(); print('«НІХТО» = 0' in report);sys.exit(any(s!='0' for s in statuses) or '«НІХТО» = 0' not in report)
PY
