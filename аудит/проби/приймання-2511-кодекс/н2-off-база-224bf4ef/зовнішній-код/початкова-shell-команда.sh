set -euo pipefail
umask 077
pack=/tmp/liusterko-off-base-package-224bf4ef
adapter="$pack/інструменти/pyodide-cpython.cjs"
sed -n '233,251p' тест_показу.js > "$pack/докази/jsdom-ізоляція.txt"
git show --no-patch --format='%H%n%P' 6e5503c97cfafeec9e209f94c330e68dacce2b28 > "$pack/докази/parent-6e5503c9.txt"
cat > "$pack/докази/команда.txt" <<EOF
cd /tmp/liusterko-off-base-build-224bf4ef/джерела
TMPDIR='$pack/тимчасове' PYTHONDONTWRITEBYTECODE=1 GIT_NO_LAZY_FETCH=1 LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON='$adapter' python3 build_артефакт.py . '$pack/index.html' показ-повний
EOF
status=0
TMPDIR="$pack/тимчасове" PYTHONDONTWRITEBYTECODE=1 GIT_NO_LAZY_FETCH=1 LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON="$adapter" python3 build_артефакт.py . "$pack/index.html" показ-повний > "$pack/докази/build.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$pack/докази/exit-code.txt"
python3 "$pack/інструменти/джерела.py" after
cmp "$pack/докази/джерела-before.json" "$pack/докази/джерела-after.json"
tail -22 "$pack/докази/build.log"
exit "$status"
