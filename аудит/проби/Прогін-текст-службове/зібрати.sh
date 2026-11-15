# зібрати.sh <тека джерел> <тека виходу>
export LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON=/root/.local/share/uv/python/cpython-3.12.1-linux-x86_64-gnu/bin/python3.12
mkdir -p "$2"; cd "$1"; python3 build_артефакт.py . "$2/index.html" показ-повний > "$2/збірка.log" 2>&1; echo "збірка rc=$? $1"
