cd wt/джерела
T="python3 ../../tm.py"
for rep in 1 2; do
$T nodecheck_$rep bash -c 'fails=0; for f in $(find . -name node_modules -prune -o -name "*.js" -print|sort); do node --check "$f" || fails=$((fails+1)); done; exit $fails'
$T pycompile_$rep bash -c 'fails=0; for f in $(find . -name node_modules -prune -o -name "*.py" -print|sort); do python3 -m py_compile "$f" || fails=$((fails+1)); done; exit $fails'
$T podil_$rep bash -c 'V=0; for f in проби/поділ_*_ast.py; do python3 "$f" || V=$((V+1)); done; exit $V'
$T unpack_$rep python3 -c "import чистка_каталогу as ч, feed as Ф; ч.забезпечити_чистим('каталог_повний.xml'); Ф.каталог_на_диску('каталог_brief.xml')"
$T dym_$rep python3 стенд_знімок.py --дим
$T zhyvyi_$rep python3 тест_живого_шляху.py
$T protokol_$rep python3 тест_протоколу.py
$T rozdily_$rep python3 прилади/розділи_гейтів.py
$T kontrakty_$rep python3 audit_contracts.py
NODE_PATH=node_modules $T pokaz_$rep node тест_показу.js
$T mist_$rep node тест_мосту.js
$T dosiazh_$rep python3 досяжність.py
done
