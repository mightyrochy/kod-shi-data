#!/usr/bin/env bash
# Справжні створення, verify й публікація: приватний start, новіший main, доробка, захисні відмови й повтор публікації позначкою.
set -eu
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"
W=$(mktemp -d "${TMPDIR:-/tmp}/bundles.XXXXXX")
"${PWSH:-pwsh}" -NoProfile -File "$(wp "$H/сценарії_бандлів.ps1")" -Root "$(wp "$W")" "$@"
