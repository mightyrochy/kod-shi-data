#!/usr/bin/env bash
# Стенд обгортки М.2 без Windows (pwsh 7, git, python3): локальний «origin», фальшивий agy (fake_agy.py) і claude.
# Один сценарій: сценарії_прогону.sh <тека> <сценарій fake_agy> <stream|print> [модель]; pwsh — змінна PWSH.
# Усі 14: for s in "a abandon_then_done stream" "b github stream" "c github_renamed stream" "d wrapper stream" \
#   "e blocked stream" "f wrong_sha stream" "g dirty stream" "h never stream" "i hang stream" "j die stream" \
#   "k nothing stream" "l abandon_then_done print" "m hang print" "n abandon_then_done stream bad-model"; do
#   set -- $s; ./сценарії_прогону.sh "$@" 2>/dev/null | grep 'GEMINI ОБГОРТКА'; done
set -u
H=$(cd "$(dirname "$0")" && pwd)
PW="${PWSH:-pwsh}"
SRC=$(cd "$H/.." && pwd)
NAME=$1; SC=$2; MODE=$3; MODEL=${4:-gemini-3.8-flash-high}; HOOK=${5:-}
W="${TMPDIR:-/tmp}/gemini-obhortka/$NAME"; rm -rf "$W"; mkdir -p "$W"/{fake,runs,out,pub}
SLUG='М.2-проба-обгортки'
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
git init -q --bare "$W/origin.git"
git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
cd "$W/seed"; git checkout -q -b main
mkdir -p аудит/наряди аудит/адаптери/gemini .github/workflows
printf 'Т | наряд\n\nЗроби щось.\n' > "аудит/наряди/$SLUG.md"
printf '| роль | сесія |\n|---|---|\n| диспетчер | session_01TEST (ДИСПЕТЧЕР) | x |\n' > аудит/СТАН.md
echo 'on: push' > .github/workflows/x.yml; echo '#' > аудит/адаптери/gemini/gemini_publish.ps1
# дані крамниць (М.9-Г): у клоні рушія їх бути не може ні в дереві, ні блобами в .git
mkdir -p джерела/дані_крамниць аудит/проби; echo 'ТЕКСТ_КРАМНИЦІ' | gzip > каталог_повний.xml.gz
echo '{"назва":"ТЕКСТ_КРАМНИЦІ"}' > джерела/дані_крамниць/фід.jsonl; echo 'ТЕКСТ_КРАМНИЦІ' > аудит/проби/сирі.txt
echo 'print(1)' > аудит/проби/проба.py
git add -A; git commit -q -m init; git push -q origin main
git push -q origin "main:refs/heads/gemini-queue/$SLUG/$MODEL/1"
# file:// і allowFilter — щоб частковий клон обгортки (М.9-Г) був справжнім, як із GitHub
git -C "$W/origin.git" config uploadpack.allowFilter true; git -C "$W/origin.git" config uploadpack.allowAnySHA1InWant true
cd "$W"; git clone -q "file://$W/origin.git" clone; git -C clone config user.name g; git -C clone config user.email g@x
export FAKE_SCENARIO=$SC FAKE_STATE="$W/fake" FAKE_CLAUDE_LOG="$W/claude.log"
GA=$(python3 -c "import json,os;print(json.dumps({**dict(RepoDir='$W/clone',RunsDir='$W/runs',OutDir='$W/out',RepoUrl='file://$W/origin.git',AgyExe='$H/fake_agy.py',CodexExe='$H/fake_codex.py',Mode='$MODE',TurnMinutes=0.05,TotalMinutes=0.5,MaxNudges=3),**json.loads(os.environ.get('EXTRA','{}'))}))")
# HOME стенду: обгортка пише ~/.codex/config.toml (профіль Codex М.9-Г)
mkdir -p "$W/home"; HOME="$W/home" "$PW" -NoProfile -File "$H/side.ps1" -Script "$SRC/gemini_run.ps1" -ArgsJson "$GA"; echo "gemini exit=$?"
[ -n "$HOOK" ] && (cd "$W" && eval "$HOOK")
PA=$(python3 -c "import json;print(json.dumps(dict(WorkDir='$W/pub',OutDir='$W/out',RepoUrl='$W/origin.git',ClaudeExe='$H/fake_claude.py',SendRetryDelaySeconds=0)))")
"$PW" -NoProfile -File "$H/side.ps1" -Script "$SRC/gemini_publish.ps1" -ArgsJson "$PA"; echo "publish exit=$?"
echo "--- out:"; ls "$W/out"; cat "$W"/out/*.json 2>/dev/null | grep -v heartbeat; echo
echo "--- wrapper.log:"; cat "$W/runs/wrapper.log"
echo "--- publish.log:"; cat "$W/pub/publish.log" 2>/dev/null
echo "--- claude:"; cat "$W/claude.log" 2>/dev/null
echo "--- клон:"; ls -R "$W/clone" | grep -c 'ТЕКСТ\|фід\|сирі\|каталог_повний' | sed 's/^/  файлів даних: /'
git -C "$W/clone" rev-list --objects --missing=print --all 2>/dev/null | grep -c '^?' | sed 's/^/  блобів поза клоном: /'
grep -rl 'ТЕКСТ_КРАМНИЦІ' "$W/clone" 2>/dev/null | wc -l | sed 's/^/  файлів дерева з текстом крамниці: /'
echo "--- origin gemini/:"; git -C "$W/origin.git" for-each-ref --format='%(refname) %(objectname)' refs/heads/gemini/
