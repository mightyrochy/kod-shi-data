# Спільне для стендів (source): Linux/macOS і Git Bash на Windows (є cygpath) з Windows PowerShell. Потребує $H — тека стенда.
# PowerShell і python — рідні програми Windows і шляху MSYS `/tmp/…` не розуміють (він стає `C:/c/…`), тож усе, що йде їм у
# JSON-аргументах, `-File` і змінних, — через wp (`cygpath -m`); заглушки .py обгортки запускають напряму, тож на Windows
# кожна має `<заглушка>.cmd` з інтерпретатором (stub). Скрипти копіюються в ASCII-теку $STUBS: cmd.exe читає .cmd в OEM-кодуванні
# і не прочитає кирилицю шляху репозиторію. Python — python3, на Windows інколи лише python.
PY=python3; python3 -c '' >/dev/null 2>&1 || PY=python
WIN=; command -v cygpath >/dev/null 2>&1 && WIN=1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
wp() { if [ -n "$WIN" ]; then cygpath -m "$1"; else printf '%s' "$1"; fi; }
STUBS="${TMPDIR:-/tmp}/gemini-stubs"
[ -n "$WIN" ] && PYX=$($PY -c 'import sys; print(sys.executable)')
stub() { if [ -n "$WIN" ]; then mkdir -p "$STUBS"; cp "$H"/fake_*.py "$STUBS/"
  printf '@"%s" "%s" %%*\r\n' "$PYX" "$(wp "$STUBS/$1.py")" > "$STUBS/$1.cmd"; wp "$STUBS/$1.cmd"
  else printf '%s' "$H/$1.py"; fi; }
