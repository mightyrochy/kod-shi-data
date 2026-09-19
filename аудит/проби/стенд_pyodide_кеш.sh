#!/bin/sh
# Офлайн-кеш Pyodide 0.26.4 для `рв6_стенд.js` (рядок 26 дошки).
#
# НАВІЩО. Стенд навмисне глушить усю мережу сторінки через `route()`: прилад
# міряє продукт, а не швидкість CDN. Єдиний виняток — `cdn.jsdelivr.net/pyodide/**`,
# і той віддається З ДИСКА, з теки, яку стенд бере четвертим аргументом
# (`ТЕКА_PYODIDE`). Поки тієї теки нема, сторінка дістає 404 на `pyodide.js`, і
# ЖОДНА звірка стенда не виконується (РВ-6 §5, БЕКЛОГ рядок 26 і §5). Цей скрипт
# наповнює теку один раз; далі стенд мережі не потребує взагалі.
#
# ЧОМУ ІМЕНА ЗМІННИХ І env ТУТ ЛАТИНИЦЕЮ, хоч усе решта кирилицею: `sh` (dash)
# не має кириличних імен змінних — ні в env, ні навіть у присвоєнні всередині
# скрипта. `ТЕКА=…` дає `not found`, а `ТЕКА_PYODIDE=… sh …` — rc 127 (виміряно
# 19.09.2026). Той самий урок уже записано в `zbirka.yml` про `LYUSTERKO_CATALOG`.
# Кирилична `ТЕКА_PYODIDE` лишається там, де вона працює, — аргументом стенда.
#
# Запуск:  sh аудит/проби/стенд_pyodide_кеш.sh /tmp/pyodide
# Друкує рядок на кожен файл і падає (rc 1), якщо бракує хоч одного.
set -eu
DIR="${1:-${PYODIDE_DIR:-/tmp/pyodide}}"
BASE="https://cdn.jsdelivr.net/pyodide/v0.26.4/full"
# Рівно ті п'ять файлів, які тягне сторінка показу: тег `<script defer …/pyodide.js>`
# і далі сам `loadPyodide` за `indexURL` (`ДЗЕРКАЛА_П` у `показ.html`).
mkdir -p "$DIR"
miss=0
for f in pyodide.js pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
  if [ -s "$DIR/$f" ]; then echo "  = $f уже в кеші ($(wc -c < "$DIR/$f") Б)"; continue; fi
  if curl -fsSL --max-time 300 -o "$DIR/$f.частина" "$BASE/$f" && [ -s "$DIR/$f.частина" ]; then
    mv "$DIR/$f.частина" "$DIR/$f"; echo "  + $f стягнуто ($(wc -c < "$DIR/$f") Б)"
  else
    rm -f "$DIR/$f.частина"; echo "  ✗ $f НЕ стягнуто"; miss=$((miss + 1))
  fi
done
echo "кеш Pyodide 0.26.4: $DIR · бракує $miss"
[ "$miss" -eq 0 ]
