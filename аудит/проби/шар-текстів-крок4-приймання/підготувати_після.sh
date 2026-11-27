#!/bin/bash
# Сторона ПІСЛЯ рецепту повтор.sh (#4848), без змін: worktree, стенд із патча, збірка.
set -eu
ROOT=/home/user/kod-shi-data; OUT=/tmp/крок4; REF=c9ff4ec95338aef71a0d608e4cc373eaa956d676
PATCH_PATH=аудит/проби/приймання-н2-782c/стенд/рв6_н2.patch
git -C "$ROOT" worktree add --detach "$OUT/код-після" "$REF"
cd "$OUT/код-після"
STAND=аудит/проби/рв6_крок4.js
patch -f -F 0 -o "$STAND" "$OUT/рв6_основа.js" < "$PATCH_PATH"
sed -i.bak 's/опис: x\.опис, опис_без_фото:/опис: x.опис, як_носити: x.як_носити, опис_без_фото:/' "$STAND"
node --check "$STAND"
mkdir -p "$OUT/стенд-після"
(cd джерела && LYUSTERKO_CATALOG=повний LYUSTERKO_PYC_PYTHON=/root/.local/share/uv/python/cpython-3.12.1-linux-x86_64-gnu/bin/python3.12 python3 build_артефакт.py . "$OUT/стенд-після/index.html" показ-повний)
echo ПІДГОТОВАНО
