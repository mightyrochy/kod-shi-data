#!/usr/bin/env bash
# Читач звіту й читання смуги.json без запуску моделей чи змін установлених копій.
set -euo pipefail
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"
"${PWSH:-pwsh}" -NoProfile -File "$(wp "$H/сценарії_звіту.ps1")" -SourceDir "$(wp "$H/..")"
