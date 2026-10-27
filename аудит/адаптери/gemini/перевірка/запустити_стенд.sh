#!/usr/bin/env bash
# Один стенд для CI й ноутбука: повний лог, підсумок і відмова при будь-якому ✗.
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd)
. "$H/середовище.sh"
mkdir -p "${TMPDIR:-/tmp}"
LOG=$(mktemp "${TMPDIR:-/tmp}/stend.XXXXXX")
trap 'rm -f "$LOG"' EXIT
bash "$H/$1" 2>&1 | tee "$LOG"
CODES=("${PIPESTATUS[@]}")
GOOD=$(grep -cE '^[[:space:]]*([a-z][0-9a-z]*: +)?(✓ |ok[[:space:]])' "$LOG" || true)
BAD=$(grep -cE '(^|[[:space:]])✗([[:space:]]|$)|^[[:space:]]*(FAIL|ПОМИЛКА)[[:space:]]' "$LOG" || true)
RC=0
if [ "${CODES[0]}" -ne 0 ] || [ "${CODES[1]}" -ne 0 ] || [ "$BAD" -ne 0 ] || [ "$GOOD" -eq 0 ]; then RC=1; fi
RESULT="✓ $GOOD / ✗ $BAD; код стенда ${CODES[0]}; код логу ${CODES[1]}"
echo "ПІДСУМОК $1: $RESULT"
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  printf '\n### %s\n\n%s\n' "$1" "$RESULT" >> "$GITHUB_STEP_SUMMARY" || RC=1
fi
exit "$RC"
