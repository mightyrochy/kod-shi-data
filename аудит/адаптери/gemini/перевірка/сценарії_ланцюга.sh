#!/usr/bin/env bash
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"
"${PWSH:-pwsh}" -NoProfile -File "$(wp "$H/сценарії_ланцюга.ps1")"
