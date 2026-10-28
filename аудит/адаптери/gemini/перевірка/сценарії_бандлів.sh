#!/usr/bin/env bash
# Справжні створення, verify й публікація: приватний start, новіший main, доробка та захисні відмови.
set -eu
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"
W=$(mktemp -d "${TMPDIR:-/tmp}/bundles.XXXXXX")
"${PWSH:-pwsh}" -NoProfile -File "$(wp "$H/сценарії_бандлів.ps1")" -Root "$(wp "$W")" "$@"
