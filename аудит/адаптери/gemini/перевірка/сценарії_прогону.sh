#!/usr/bin/env bash
# Стенд обгортки М.2 без Windows (pwsh 7, git, python3): локальний «origin», фальшивий agy (fake_agy.py) і claude.
# Один сценарій: сценарії_прогону.sh <тека> <сценарій fake_agy> <stream|print> [модель]; pwsh — змінна PWSH.
# Усі 14: for s in "a abandon_then_done stream" "b github stream" "c github_renamed stream" "d wrapper stream" \
#   "e blocked stream" "f wrong_sha stream" "g dirty stream" "h never stream" "i hang stream" "j die stream" \
#   "k nothing stream" "l abandon_then_done print" "m hang print" "n abandon_then_done stream bad-model"; do
#   set -- $s; ./сценарії_прогону.sh "$@" 2>/dev/null | grep 'GEMINI ОБГОРТКА'; done
set -u
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"
PW="${PWSH:-pwsh}"
SRC=$(cd "$H/.." && pwd)
# Без аргументів — усі випадки стенда; з аргументами — один прогін для сусідніх стендів.
if [ "$#" -eq 0 ]; then
  BAD=0
  while read -r name scenario mode want model; do
    LOG=$(mktemp "${TMPDIR:-/tmp}/prohin.XXXXXX")
    bash "$0" "ci-$name" "$scenario" "$mode" "${model:-gemini-3.8-flash-high}" > "$LOG" 2>&1
    RC=$?
    if [ "$want" = ГОТОВО ]; then
      EXPECT='GEMINI ОБГОРТКА: ГОТОВО gemini/М.2-проба-обгортки '
    else
      EXPECT="GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/М.2-проба-обгортки $want"
    fi
    GOT=$(delivered "${TMPDIR:-/tmp}/gemini-obhortka/ci-$name/claude.log" 2>/dev/null)
    if [ "$RC" -eq 0 ] && [[ "$GOT" == *"$EXPECT"* ]]; then
      echo "  ✓ $name ($scenario, $mode)"
    else
      echo "  ✗ $name ($scenario, $mode), код $RC, очікування $want"
      cat "$LOG"
      BAD=1
    fi
    rm -f "$LOG"
  done <<'CASES'
a abandon_then_done stream ГОТОВО
b github stream GITHUB_DIR
c github_renamed stream GITHUB_DIR
d wrapper stream WRAPPER_FILES
e blocked stream BLOCKED_PUBLISHED
f wrong_sha stream ГОТОВО
g dirty stream ГОТОВО
h never stream NO_REPORT
i hang stream ГОТОВО
j die stream ГОТОВО
k nothing stream BLOCKED
l abandon_then_done print ГОТОВО
m hang print TIMEOUT_PUBLISHED
n abandon_then_done stream MODEL_INVALID bad-model
CASES
  exit "$BAD"
fi
NAME=$1; SC=$2; MODE=$3; MODEL=${4:-gemini-3.8-flash-high}; HOOK=${5:-}
W="${TMPDIR:-/tmp}/gemini-obhortka/$NAME"; rm -rf "$W"; mkdir -p "$W"/{fake,runs,out,pub}
SLUG='М.2-проба-обгортки'
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
git init -q --bare "$W/origin.git"
git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
cd "$W/seed"; git checkout -q -b main
mkdir -p аудит/наряди аудит/адаптери/gemini .github/workflows
printf 'Т | наряд\n\n%sЗроби щось.\n%s' "${TASK_ROLE:+Роль — $TASK_ROLE (\`аудит/$TASK_ROLE.md\`), ядро — \`AGENTS.md\`. Наряд самодостатній.
}" "${TASK_TAIL:-}" > "аудит/наряди/$SLUG.md"
printf '| роль | сесія |\n|---|---|\n| диспетчер | session_01TEST (ДИСПЕТЧЕР) | x |\n' > аудит/СТАН.md
echo 'on: push' > .github/workflows/x.yml; echo '#' > аудит/адаптери/gemini/gemini_publish.ps1
git add -A; git commit -q -m init; git push -q origin main
git push -q origin "main:refs/heads/gemini-queue/$SLUG/$MODEL/1"
cd "$W"; git clone -q origin.git clone; git -C clone config user.name g; git -C clone config user.email g@x
export FAKE_SCENARIO=$SC FAKE_STATE="$(wp "$W/fake")" FAKE_CLAUDE_LOG="$(wp "$W/claude.log")"
GA=$($PY -c "import json,os;print(json.dumps({**dict(RepoDir='$(wp "$W/clone")',RunsDir='$(wp "$W/runs")',OutDir='$(wp "$W/out")',RepoUrl='$(wp "$W/origin.git")',AgyExe='$(stub fake_agy)',CodexExe='$(stub fake_codex)',Mode='$MODE',TurnMinutes=0.05,TotalMinutes=0.5,MaxNudges=3),**json.loads(os.environ.get('EXTRA','{}'))}))")
"$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "$GA"; echo "gemini exit=$?"
[ -n "$HOOK" ] && (cd "$W" && eval "$HOOK")
PA=$($PY -c "import json;print(json.dumps(dict(WorkDir='$(wp "$W/pub")',OutDir='$(wp "$W/out")',RepoUrl='$(wp "$W/origin.git")',ClaudeExe='$(stub fake_claude)',SendRetryDelaySeconds=0)))")
"$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "$PA"; echo "publish exit=$?"
echo "--- out:"; ls "$W/out"; cat "$W"/out/*.json 2>/dev/null | grep -v heartbeat; echo
echo "--- wrapper.log:"; cat "$W/runs/wrapper.log"
echo "--- publish.log:"; cat "$W/pub/publish.log" 2>/dev/null
echo "--- claude:"; cat "$W/claude.log" 2>/dev/null
echo "--- origin gemini/:"; git -C "$W/origin.git" for-each-ref --format='%(refname) %(objectname)' refs/heads/gemini/

exit 0
