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
# Windows PowerShell на ноутбуці не виконує `-File` без -ExecutionPolicy Bypass (політика «скрипти вимкнено»): без PWSH —
# обгортка в $STUBS, що дописує ключ; TMPDIR — лише ASCII (кирилиця в шляху ламає .cmd заглушок).
if [ -n "$WIN" ] && [ -z "${PWSH:-}" ]; then mkdir -p "$STUBS"; printf '#!/bin/sh\nexec powershell -ExecutionPolicy Bypass "$@"\n' > "$STUBS/pwb"
  chmod +x "$STUBS/pwb"; export PWSH="$STUBS/pwb"; fi

# Доставлений рядок перевіряємо з JSON-журналу заглушки, а не з діагностичного stdout різних процесів.
delivered() { $PY - "$(wp "$1")" <<'P'
import json, sys
with open(sys.argv[1], encoding='utf-8') as stream:
    for line in stream:
        print(json.loads(line)['stdin'])
P
}
