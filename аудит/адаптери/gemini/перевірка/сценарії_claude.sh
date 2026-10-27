#!/usr/bin/env bash
# Стенд рушія Claude (claude_run.ps1): позначки cc-, коди кінця, продовження, перерваний прогін, вимкнення, стан у issue
# (fake_gh.py), доставка рядка ВИМКНЕНО (gemini_publish.ps1) і gemini-run, що не бере cc-. PowerShell — PWSH (pwsh 7 чи
# на ноутбуці Git Bash + `PWSH=powershell`); git, Python 3 (python3, інакше python). Код 1, якщо хоч одна перевірка ✗.
# Тека прогону — ${TMPDIR:-/tmp}/claude-run/<випадок>. Шляхи й заглушки на Windows — спільне `середовище.sh` (wp, stub).
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"; PW="${PWSH:-pwsh}"; SRC=$(cd "$H/.." && pwd)
SLUG='проба-рушія-claude'; M=cc-claude-sonnet-5-5-medium; BAD=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
alive() { $PY -c "import os, subprocess, sys
pid = int(open(sys.argv[1]).read())
if os.name == 'nt': sys.exit(0 if (' %d ' % pid) in subprocess.run(['tasklist', '/FI', 'PID eq %d' % pid, '/NH'], capture_output=True, text=True).stdout else 1)
try: os.kill(pid, 0)
except OSError: sys.exit(1)" "$(wp "$1")"; }
kill_pid() { [ -e "$1" ] && $PY -c "import os, signal, sys; os.kill(int(open(sys.argv[1]).read()), signal.SIGTERM)" "$(wp "$1")" 2>/dev/null; }
setup() { W="${TMPDIR:-/tmp}/claude-run/$1"; rm -rf "$W"; mkdir -p "$W"/{cr,out,pub,gem,gh,runs}
  git init -q --bare "$W/origin.git"; git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
  (cd "$W/seed"; git checkout -q -b main; mkdir -p аудит/наряди; printf 'Т | наряд\n\nПідніми й зупини LM Studio.\n' > "аудит/наряди/$SLUG.md"
   printf '| диспетчер | session_01TEST |\n' > аудит/СТАН.md; git add -A; git commit -q -m init; git push -q origin main 2>/dev/null)
  git clone -q "$W/origin.git" "$W/clone" 2>/dev/null; git -C "$W/clone" config user.name g; git -C "$W/clone" config user.email g@x
  export FAKE_CC_LOG="$(wp "$W/cc.log")" FAKE_GH_DIR="$(wp "$W/gh")" FAKE_CC_SCENARIO=done FAKE_BOOT=b1 FAKE_GEMINI_STATE= \
    FAKE_CLAUDE_LOG="$(wp "$W/claude.log")" FAKE_ISOLATION=
  printf 'b1' > "$W/cr/boot.txt"; }
mark() { git -C "$W/seed" push -q origin "${2:-main}:refs/heads/gemini-queue/$1" 2>/dev/null; }
cr() { A=$($PY -c "import json,sys;print(json.dumps({**dict(WorkDir='$(wp "$W/cr")',RepoDir='$(wp "$W/clone")',OutboxDir='$(wp "$W/out")',PublishDir='$(wp "$W/pub")',GeminiOutDir='$(wp "$W/gem")',RepoUrl='$(wp "$W/origin.git")',ClaudeExe='$(stub fake_cc)',GhExe='$(stub fake_gh)',HangMinutes=0.05,OffWaitMinutes=0.05),**json.loads(sys.argv[1])}, ensure_ascii=False))" "${1:-{\}}")
  "$PW" -NoProfile -File "$(wp "$H/side_claude.ps1")" -Script "$(wp "$SRC/claude_run.ps1")" -ArgsJson "$A" >/dev/null 2>&1; }
lines() { cat "$W"/out/*.txt 2>/dev/null; }
nlines() { ls "$W/out" | grep -c '\.txt$'; }
argv() { $PY -c "import json
for l in open('$(wp "$W/cc.log")', encoding='utf-8'): print(' '.join(json.loads(l)['argv']))" 2>/dev/null | tail -1; }
prompt() { $PY -c "import json
print([json.loads(l) for l in open('$(wp "$W/cc.log")', encoding='utf-8')][-1]['stdin'])" 2>/dev/null; }
chk() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; BAD=1; fi; }
code() { setup "$1"; mark "$SLUG/${3:-$M}/1"; FAKE_CC_SCENARIO=$2 cr "${5:-}"; WANT=$4
  EXPECTED="GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$SLUG $WANT"
  case "$WANT" in AUTH) EXPECTED="$EXPECTED"$'\n''GEMINI ОБГОРТКА: ТРИВОГА AUTH CLAUDE';;
    ENGINE_MISSING) EXPECTED="$EXPECTED"$'\n''GEMINI ОБГОРТКА: ТРИВОГА ENGINE CLAUDE';; esac
  chk "$2 → підсумок $4 і окрема тривога за потреби (є: $(lines))" '[ "$(lines | LC_ALL=C sort)" = "$(printf "%s\n" "$EXPECTED" | LC_ALL=C sort)" ]'; }

echo "=== К1 ГОТОВО: модель і зусилля дослівно, auto, промпт запускача, SHA з origin, стан в issue"
setup k1; mark "$SLUG/$M/1"; cr
SHA=$(git -C "$W/origin.git" rev-parse "refs/heads/claude/$SLUG" 2>/dev/null)
chk "рядок ГОТОВО claude/<наряд> <SHA origin> МОДЕЛЬ $M" '[ -n "$SHA" ] && [ "$(lines)" = "GEMINI ОБГОРТКА: ГОТОВО claude/$SLUG $SHA МОДЕЛЬ $M" ]'
chk "argv: -p --model claude-sonnet-5-5 --effort medium --permission-mode auto stream-json" '[ "$(argv)" = "-p --model claude-sonnet-5-5 --effort medium --permission-mode auto --output-format stream-json --verbose" ]'
chk "промпт: НОУТБУК.md, наряд дослівно, вимикає лише обгортка, без «Продовжуй»" 'P=$(prompt); [[ "$P" == *"аудит/НОУТБУК.md"* && "$P" == *"Підніми й зупини LM Studio."* && "$P" == *"вимикає лише обгортка за позначкою"* && "$P" != *"Продовжуй"* && "$P" != *"запускач —"* ]]'
chk "issue 1856 оновлено PATCH-ем, тіло — «веде наряд» і позначка" 'tr -d "\r" < "$W/gh/calls.log" | grep -q "^PATCH repos/mightyrochy/kod-shi-data/issues/1856$" && grep -l "веде наряд" "$W"/gh/patch_*.json | xargs grep -q "gemini-queue/$SLUG/$M/1"'
chk "події stream-json — у events.tsv" '[ "$(cat "$W"/cr/runs/*/events.tsv | wc -l)" = 3 ]'
cr; chk "другий прохід ту саму позначку не бере" '[ "$(nlines)" = 1 ] && [ "$(wc -l < "$W/cc.log")" = 1 ]'
echo "=== К2 нова спроба при наявній гілці — «Продовжуй з гілки»; модель без зусилля — без --effort"
mark "$SLUG/cc-claude-opus-5-5/2"; cr
chk "промпт: Продовжуй з гілки claude/<наряд>" '[[ "$(prompt)" == *"Продовжуй з гілки \`claude/$SLUG\`"* ]]'
chk "argv без --effort" '[ "$(argv)" = "-p --model claude-opus-5-5 --permission-mode auto --output-format stream-json --verbose" ]'
echo "=== К3 коди кінця"
code k3a wrong_sha "$M" NO_PUSH
code k3b bad_branch "$M" BAD_BRANCH
code k3c blocked "$M" BLOCKED
chk "гілка зі звіту ЗАБЛОКОВАНО збережена для продовження" '[ "$(cat "$W"/cr/state/branch-*.txt)" = "claude/$SLUG" ]'
code k3d no_report "$M" NO_REPORT
code k3e die "$M" EXIT
code k3f hang "$M" HANG
chk "завислий claude зупинено" '[ -e "$W/cc.log.pid" ] && ! alive "$W/cc.log.pid"'
code k3g effort cc-claude-sonnet-5-5-ultra EFFORT_INVALID
code k3h auth "$M" AUTH
code k3i quota "$M" QUOTA0_CLAUDE_M10
chk "ліміт: позначка чекає скидання (WAIT), спроба не спалена" 'grep -q "^WAIT " "$W"/cr/state/*.txt'
code k3j bad_model cc-claude-sonnet-9 MODEL_INVALID
code k3k done "$M" ENGINE_MISSING "{\"ClaudeExe\":\"$(wp "$W")/нема/claude\"}"
setup k3l; mark "нема-наряду/$M/1"; cr; chk "нема файлу наряду → NO_TASK_FILE" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/нема-наряду NO_TASK_FILE" ]'
setup k3m; S=$(git -C "$W/seed" commit-tree "$(git -C "$W/seed" rev-parse 'main^{tree}')" -p main -m збоку); mark "$SLUG/$M/1" "$S"; cr
chk "коміт позначки не в main → NOT_ON_MAIN, claude не кликано" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$SLUG NOT_ON_MAIN" ] && [ ! -e "$W/cc.log" ]'
setup k3n; mark "$SLUG/$M/1"; cr '{"MarkerMaxAgeDays":-1}'; chk "стара позначка — без рядка й без claude" '[ "$(nlines)" = 0 ] && [ ! -e "$W/cc.log" ] && grep -qx STALE "$W"/cr/state/*.txt'
echo "=== К4 claude закінчився, а нащадок тримає stdout — не завислість"
setup k4; mark "$SLUG/$M/1"; T0=$(date +%s); FAKE_CC_SCENARIO=child_holds_stdout cr '{"HangMinutes":5}'; T1=$(date +%s)
chk "ГОТОВО за ≤ 90 с (є: $((T1 - T0)) с)" '[[ "$(lines)" == "GEMINI ОБГОРТКА: ГОТОВО claude/$SLUG "* ]] && [ $((T1 - T0)) -le 90 ]'
kill_pid "$W/cc.log.child"
echo "=== К5 прогін, перерваний вимкненням: наступний прохід пише INTERRUPTED"
setup k5; mkdir -p "$W/cr/state"; printf 'STARTED 20261026-120000-0123456789ab {"pid":999999,"start":"x","marker":"gemini-queue/%s/%s/1"}' "$SLUG" "$M" > "$W/cr/state/x.txt"; cr
chk "рядок INTERRUPTED, стан DONE" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$SLUG INTERRUPTED" ] && grep -q "^DONE 20261026-120000-0123456789ab INTERRUPTED" "$W/cr/state/x.txt"'
echo "=== К6 ВИМКНИ-НОУТБУК"
setup k6; mark "ВИМКНИ-НОУТБУК/cc-off/1"; MS=$(git -C "$W/seed" rev-parse main); FAKE_GEMINI_STATE=Running cr
chk "gemini-run виконується — без рядка й без shutdown" '[ "$(nlines)" = 0 ] && [ ! -e "$W/cr/shutdown.txt" ]'
FAKE_GEMINI_STATE='?'; printf '{"time":"2026-10-26T12:00:00","isolation":"OK","marker":"gemini-queue/x/gemini-3.5-flash/1","engine":"agy","model":"gemini-3.5-flash","since":"2026-10-26T11:50:00"}' > "$W/gem/heartbeat.json"; cr
chk "стан задачі не видно, у heartbeat узята позначка — чекає" '[ "$(nlines)" = 0 ] && [ ! -e "$W/cr/shutdown.txt" ]'
chk "issue: рядок gemini-run з позначкою й рушієм" 'grep -h "gemini-queue/x/gemini-3.5-flash/1" "$W"/gh/patch_*.json | grep -q "agy"'
rm "$W/gem/heartbeat.json"; FAKE_GEMINI_STATE=Ready cr
chk "рушії вільні — ВИМКНЕНО <SHA коміту>, shutdown" '[ "$(lines)" = "GEMINI ОБГОРТКА: ВИМКНЕНО $MS" ] && [ -e "$W/cr/shutdown.txt" ]'
"$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "{\"WorkDir\":\"$(wp "$W/pub")\",\"OutDir\":\"$(wp "$W/gem")\",\"OutboxDir\":\"$(wp "$W/out")\",\"RepoUrl\":\"$(wp "$W/origin.git")\",\"ClaudeExe\":\"$(stub fake_claude)\",\"SendRetryDelaySeconds\":0}" >/dev/null 2>&1
chk "gemini-publish доставляє ВИМКНЕНО диспетчерові" 'grep -q "ВИМКНЕНО $MS" "$W/claude.log"'
rm -f "$W/cr/shutdown.txt"; FAKE_BOOT=b2 cr
chk "та сама виконана позначка після нового ввімкнення — один BOOT, без shutdown" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/ВИМКНИ-НОУТБУК BOOT" ] && [ ! -e "$W/cr/shutdown.txt" ]'
FAKE_BOOT=b2 cr; chk "наступний прохід — нічого нового" '[ "$(nlines)" = 1 ] && [ ! -e "$W/cr/shutdown.txt" ]'
setup k6b; rm "$W/cr/boot.txt"; mark "ВИМКНИ-НОУТБУК/cc-off/1"; cr
chk "позначка до першого проходу після ввімкнення → BOOT, без shutdown" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/ВИМКНИ-НОУТБУК BOOT" ] && [ ! -e "$W/cr/shutdown.txt" ]'
mark "ВИМКНИ-НОУТБУК/cc-off/2"; cr; chk "наступна спроба — вимикає" '[ -e "$W/cr/shutdown.txt" ]'
echo "=== К7 gemini-run позначок cc- не бере й узятими не позначає"
setup k7; mark "$SLUG/$M/1"
"$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "{\"RepoDir\":\"$(wp "$W/clone")\",\"RunsDir\":\"$(wp "$W/runs")\",\"OutDir\":\"$(wp "$W/gem")\",\"RepoUrl\":\"$(wp "$W/origin.git")\",\"AgyExe\":\"$(stub fake_agy)\",\"TurnMinutes\":0.05,\"TotalMinutes\":0.5,\"MaxNudges\":3}" >/dev/null 2>&1
chk "gemini-run пройшов (heartbeat, ізоляція OK) — без стану й результату" 'grep -q "\"isolation\":\"OK\"" "$W/gem/heartbeat.json" && [ -z "$(ls "$W/runs/state" 2>/dev/null)" ] && [ -z "$(ls "$W/gem" | grep -vE "heartbeat|pools")" ]'
cr; chk "той самий прохід claude-run бере її" '[[ "$(lines)" == "GEMINI ОБГОРТКА: ГОТОВО claude/$SLUG "* ]]'
echo "=== К8 завислість — від останньої прийнятої події stream-json, доки процес живий"
setup k8a; mark "$SLUG/$M/1"; T0=$(date +%s); FAKE_CC_SCENARIO=closed cr; T1=$(date +%s)
chk "stdout і stderr закрито, процес мовчить → HANG за ≤ 60 с (є: $((T1 - T0)) с, $(lines))" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$SLUG HANG" ] && [ $((T1 - T0)) -le 60 ]'
chk "процес після HANG зупинено" '[ -e "$W/cc.log.pid" ] && ! alive "$W/cc.log.pid"'
setup k8b; mark "$SLUG/$M/1"; FAKE_CC_SCENARIO=noise cr
chk "не-JSON рядки таймера не скидають → HANG (є: $(lines))" '[ "$(lines)" = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$SLUG HANG" ]'
chk "events.tsv — лише події з типом (2), шум — у claude.jsonl" '[ "$(cat "$W"/cr/runs/*/events.tsv | wc -l)" = 2 ] && ! cut -f2 "$W"/cr/runs/*/events.tsv | tr -d "\r" | grep -qx "" && grep -q "^шум 0" "$W"/cr/runs/*/claude.jsonl'
setup k8c; mark "$SLUG/$M/1"; FAKE_CC_SCENARIO=pause cr
chk "події частіше за поріг, усього довше за нього → ГОТОВО (є: $(lines))" '[[ "$(lines)" == "GEMINI ОБГОРТКА: ГОТОВО claude/$SLUG "* ]]'
echo; [ $BAD = 0 ] && echo "ВСЕ ✓" || echo "ЗБІЙ ✗"; exit $BAD
