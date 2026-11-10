#!/usr/bin/env bash
# Залежності Chromium для Playwright без шрифтових пакетів CJK/Thai/unifont/xfonts (13310–13314).
# Причина (вимір 04–05.11, журнали кроку): `playwright install --with-deps` тягне 6 шрифтових пакетів (~17 МБ) з
# azure.archive.ubuntu.com; на повільному дзеркалі це 5–10 хв (14:00–16:00 UTC 05.11), npm ci і завантаження chromium —
# секунди. Решта пакетів — маленькі бібліотеки, на раннері зазвичай уже стоять. Кирилицю й емодзі дають
# fonts-liberation і fonts-noto-color-emoji — вони лишаються.
# Використання: zalezhnosti-brauzera.sh <команда playwright, можливо з аргументами>
set -euo pipefail
pw=("$@")
[ "${#pw[@]}" -gt 0 ] || { echo "потрібна команда playwright" >&2; exit 2; }
skip='^(fonts-ipafont-gothic|fonts-wqy-zenhei|fonts-tlwg-loma-otf|fonts-freefont-ttf|fonts-unifont|xfonts-.*)$'
missing=$("${pw[@]}" install-deps --dry-run chromium 2>&1 || true)
echo "$missing"
pkgs=$(printf '%s\n' "$missing" | sed -n 's/^  \([^ ]\+\)$/\1/p' | grep -Ev "$skip" || true)
if [ -n "$pkgs" ]; then
  opts=(-o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30)
  # shellcheck disable=SC2086
  sudo apt-get "${opts[@]}" install -y --no-install-recommends $pkgs \
    || { sudo apt-get "${opts[@]}" update && sudo apt-get "${opts[@]}" install -y --no-install-recommends $pkgs; }
fi
"${pw[@]}" install chromium
