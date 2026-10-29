#!/usr/bin/env bash
# Стенд смуг (М.9-Е): шість позначок на одному коміті — по дві Codex, agy і Claude Code, одна з них GPU, пріоритети
# різні, одна agy (Gemini 4 Argon) — на нульовій квоті; /usage — у форматі живого agy 1.4.7. Підроблені CLI тримають
# наряд FAKE_HOLD с і пишуть start/end у часову лінію — з неї міряємо, що йшло водночас.
#   ДО:    LANES_MODE=do SRC=<тека зі старими gemini_run.ps1 і claude_run.ps1> — позначки без умов (старі скрипти умов не
#          знають), проходи, як задачі планувальника: gemini-run і claude-run водночас, кожен по позначці за прохід.
#   ПІСЛЯ: ці скрипти — планувальники gemini-run і claude-run водночас; прохід після «скидання» квоти без нової позначки;
#          дві GPU-позначки різних облікових записів; слоти з смуги.json на origin/main — 1, потім 2, без перевстановлення.
# PowerShell — PWSH (на ноутбуці Git Bash + обгортка `powershell -ExecutionPolicy Bypass`); Python 3. Код 1, якщо хоч один ✗.
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"; PW="${PWSH:-pwsh}"; SRC="${SRC:-$(cd "$H/.." && pwd)}"
MODE="${LANES_MODE:-pislia}"; HOLD="${FAKE_HOLD:-8}"; BAD=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
CX=gpt-6.1-sol-high; AG=gemini-3.8-flash-high; AQ=gemini-4-argon-high; CC=cc-claude-sonnet-5-5-medium
chk() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; BAD=1; fi; }
setup() { W="${TMPDIR:-/tmp}/smuhy/$1"; rm -rf "$W"; mkdir -p "$W"/{fake,gr,gout,cr,cout,pub,gh,lanes}
  git init -q --bare "$W/origin.git"; git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
  (cd "$W/seed"; git checkout -q -b main; mkdir -p аудит/наряди
   for s in а-codex б-codex в-agy г-agy-квота д-claude е-claude-gpu gpu-agy gpu-claude n-codex-1 n-codex-2 n-codex-3 n-codex-4; do
     printf 'Т | наряд %s\n\nЗроби щось.\n' "$s" > "аудит/наряди/$s.md"; done
   printf '| диспетчер | session_01TEST |\n' > аудит/СТАН.md; git add -A; git commit -q -m init; git push -q origin main 2>/dev/null)
  for c in clone-g clone-c; do git clone -q "$W/origin.git" "$W/$c" 2>/dev/null; git -C "$W/$c" config user.name g; git -C "$W/$c" config user.email g@x; done
  export FAKE_STATE="$(wp "$W/fake")" FAKE_TIMELINE="$(wp "$W/timeline.txt")" FAKE_HOLD="$HOLD" FAKE_SCENARIO=commit_done \
    FAKE_CC_SCENARIO=done FAKE_CC_RL=1 FAKE_USAGE=live FAKE_CC_LOG="$(wp "$W/cc.log")" FAKE_GH_DIR="$(wp "$W/gh")" FAKE_BOOT=b1 \
    FAKE_GEMINI_STATE= FAKE_CLAUDE_LOG="$(wp "$W/claude.log")" FAKE_ISOLATION=
  printf 'b1' > "$W/cr/boot.txt"; }
# смуги.json v2: кожен слот з джерелом-виміром (без джерела обгортка бере попереднє значення).
lanes() { local s='"джерело":"вимір: стенд 29.10 — 3 копії"'
  printf '{"v":2,"slots":{"codex":{"n":%s,%s},"agy":{"n":%s,%s},"claude":{"n":%s,%s}}}\n' "$1" "$s" "$2" "$s" "$3" "$s"; }
mark() { git -C "$W/seed" push -q origin "main:refs/heads/gemini-queue/$1" 2>/dev/null; }
gem() { A=$($PY -c "import json,sys
d=dict(RepoDir='$(wp "$W/clone-g")',RunsDir='$(wp "$W/gr")',OutDir='$(wp "$W/gout")',RepoUrl='$(wp "$W/origin.git")',AgyExe='$(stub fake_agy)',CodexExe='$(stub fake_codex)',EnableCodex=True,TurnMinutes=1,TotalMinutes=2,MaxNudges=2,CodexStallMinutes=1)
if sys.argv[1]!='do': d.update(LaneDir='$(wp "$W/lanes")',PollMinutes=0.05,UsageMinutes=0,QuotaWaitMinutes=1)
print(json.dumps(d,ensure_ascii=False))" "$MODE")
  "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "$A" >/dev/null 2>&1; }
cr() { A=$($PY -c "import json,sys
d=dict(WorkDir='$(wp "$W/cr")',RepoDir='$(wp "$W/clone-c")',OutboxDir='$(wp "$W/cout")',PublishDir='$(wp "$W/pub")',GeminiOutDir='$(wp "$W/gout")',RepoUrl='$(wp "$W/origin.git")',ClaudeExe='$(stub fake_cc)',GhExe='$(stub fake_gh)',HangMinutes=1,StatusMinutes=0)
if sys.argv[1]!='do': d.update(LaneDir='$(wp "$W/lanes")',PollMinutes=0.05)
print(json.dumps(d,ensure_ascii=False))" "$MODE")
  "$PW" -NoProfile -File "$(wp "$H/side_claude.ps1")" -Script "$(wp "$SRC/claude_run.ps1")" -ArgsJson "$A" >/dev/null 2>&1; }
pub() { "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "{\"WorkDir\":\"$(wp "$W/pub")\",\"OutDir\":\"$(wp "$W/gout")\",\"OutboxDir\":\"$(wp "$W/cout")\",\"RepoUrl\":\"$(wp "$W/origin.git")\",\"ClaudeExe\":\"$(stub fake_claude)\",\"SendRetryDelaySeconds\":0}" >/dev/null 2>&1; }
# Часова лінія: найбільше водночас — усього, у смузі (за префіксом слагу), між GPU-слагами; порядок старту.
tl() { $PY - "$(wp "$W/timeline.txt")" "$1" <<'P'
import sys, collections
ev = []
for l in open(sys.argv[1], encoding='utf-8'):
    k, s, t = l.split(); ev.append((int(t), 0 if k == 'end' else 1, s))
ev.sort()
lane = lambda s: 'gpu' if s.startswith('gpu') or s.endswith('-gpu') else ('codex' if 'codex' in s else 'agy' if 'agy' in s else 'claude')
cur = collections.Counter(); mx = collections.Counter(); tot = 0; mxt = 0; order = []
for t, k, s in ev:
    d = 1 if k else -1; tot += d; mxt = max(mxt, tot)
    for g in {lane(s), 'codex' if 'codex' in s else 'agy' if 'agy' in s else 'claude'}:
        cur[g] += d; mx[g] = max(mx[g], cur[g])
    if k: order.append(s)
want = sys.argv[2]
if want == 'order': print(' '.join(order))
elif want == 'total': print(mxt)
else: print(mx[want])
P
}
# Рядки, доставлені диспетчерові (gemini-publish -> підроблений claude).
lines() { tr -d '\r' < "$W/claude.log" 2>/dev/null | $PY -c "import sys,json
for l in sys.stdin: print(json.loads(l)['stdin'])" 2>/dev/null | tr -d '\r'; }
# Порядок узяття пише планувальник після виділення слота. Старт CLI у паралельних процесах може йти в іншому порядку.
# Старі скрипти в режимі ДО не мають слотів; там показуємо їхні записи старту, як раніше.
claims() { {
  if [ "$MODE" = do ]; then
    grep -h 'слот .*-> \|наряд gemini-queue/.* -> ' "$W/gr/wrapper.log" 2>/dev/null
    grep -h 'старт ' "$W/cr/claude-run.log" 2>/dev/null
  else
    grep -h 'слот .*пріоритет .* -> ' "$W/gr/wrapper.log" "$W/cr/claude-run.log" 2>/dev/null
  fi
} | sed -E 's/^.*(gemini-queue\/[^ :]+).*$/\1/' | tr '\n' ' '; }

if [ "$MODE" = do ]; then
  echo "=== ДО: шість позначок на одному коміті (без умов: старі скрипти їх не знають), Argon — 0 % у форматі живого /usage"
  setup do; export FAKE_ZERO_UNTIL=$(( $(date +%s) + 3600 ))
  for m in "а-codex/$CX/1" "б-codex/$CX/1" "в-agy/$AG/1" "г-agy-квота/$AQ/1" "д-claude/$CC/1" "е-claude-gpu/$CC/1"; do mark "$m"; done
  T0=$(date +%s); for i in 1 2 3 4 5; do gem & cr & wait; done; T1=$(date +%s); pub
  echo "  проходів 5 (по 1 позначці на рушій за прохід), $((T1 - T0)) с"
  echo "  найбільше водночас: усього $(tl total), codex $(tl codex), agy $(tl agy), claude $(tl claude)"
  echo "  порядок узяття: $(claims)"
  echo "  кінці: $(lines | grep -v ПУЛИ | sed 's/GEMINI ОБГОРТКА: //' | sed -E 's/ [0-9a-f]{40}//' | tr '\n' ';')"
  echo "  стан ноутбука (останнє тіло issue): $(ls "$W"/gh/patch_*.json 2>/dev/null | wc -l) правок; смуги/слоти/квота — $(cat "$W"/gh/patch_*.json 2>/dev/null | grep -c 'Смуги\|Квота (UTC)')"
  exit 0
fi

echo "=== А: шість позначок на одному коміті — смуги водночас, до N у смузі, за пріоритетом; Argon на 0 % чекає скидання"
setup a; export FAKE_ZERO_UNTIL=$(( $(date +%s) + 45 ))
for m in "а-codex/$CX/1/p2" "б-codex/$CX/1/p1" "в-agy/$AG/1/p3" "г-agy-квота/$AQ/1/p0" "д-claude/$CC/1/p4" "е-claude-gpu/$CC/1/p1-gpu"; do mark "$m"; done
T0=$(date +%s); gem & cr & wait; T1=$(date +%s)
echo "  перший прохід планувальників: $((T1 - T0)) с; найбільше водночас: усього $(tl total), codex $(tl codex), agy $(tl agy), claude $(tl claude)"
chk "codex — 2 водночас (слотів 2)" '[ "$(tl codex)" = 2 ]'
chk "claude — 2 водночас (слотів 2)" '[ "$(tl claude)" = 2 ]'
chk "смуги водночас: усього ≥ 5" '[ "$(tl total)" -ge 5 ]'
C=$(claims); echo "  порядок узяття: $C"
chk "узято за пріоритетом: б(p1) раніше за а(p2), е(p1) раніше за д(p4)" '[[ "$C" == *"б-codex"*"а-codex"* && "$C" == *"е-claude-gpu"*"д-claude"* ]]'
chk "Argon (p0) на нулі не взято, позначка в чеканні" '! grep -q "г-agy-квота.*-> " "$W/gr/wrapper.log" && grep -l "^WAIT " "$W"/gr/state/*.txt >/dev/null'
S=$(cat "$W"/gh/patch_*.json | $PY -c "import sys,json
for l in sys.stdin.read().replace('}{','}\n{').splitlines(): print(json.loads(l)['body'])")
chk "стан: таблиця смуг — claude 2/2 і codex 2/2 у якійсь правці" '[[ "$S" == *"| claude | 2 | 2 |"* && "$S" == *"| codex | 2 | 2 |"* ]]'
chk "стан: квота agy з UTC — GEMINI4ARGON 0 %, скидання …Z, зчитано …Z" 'echo "$S" | grep -qE "^\| agy · GEMINI4ARGON \| WEEK \| 0 % \| 20[0-9-]+T[0-9:]+Z \| 20[0-9-]+T[0-9:]+Z \|$"'
chk "стан: квота Claude з rate_limit_event (5H, 7D)" 'echo "$S" | grep -qE "^\| claude \| 5H \| 68 % \|" && echo "$S" | grep -qE "^\| claude \| 7D \| 18 % \|"'
chk "стан: позначка Argon у «Чекають скидання квоти»" 'echo "$S" | grep -qE "^\| gemini-queue/г-agy-квота/$AQ/1/p0 \| 20[0-9-]+T[0-9:]+Z \| GEMINI4ARGON \|$"'
chk "стан: GPU зайнята слотом claude" '[[ "$S" == *"GPU: зайнята — claude-"* ]]'
echo "$S" | awk '/### Смуги/{f=1} /### Чекають/{f=2} f' | head -30 | sed 's/^/    /' > "$W/status_snapshot.txt"
pub; L=$(lines)
NQ=$(echo "$L" | grep -c "ЗАБЛОКОВАНО gemini/г-agy-квота QUOTA0_GEMINI4ARGON_M")
chk "Argon: рядок QUOTA0_GEMINI4ARGON_M<хв> диспетчерові — один (є: $NQ)" '[ "$NQ" = 1 ]'
while [ "$(date +%s)" -le "$FAKE_ZERO_UNTIL" ]; do sleep 2; done
gem; pub; L=$(lines)
chk "після «скидання» Argon узято тією ж смугою без нової позначки → ГОТОВО" '[ "$(git -C "$W/origin.git" for-each-ref refs/heads/gemini-queue | grep -c agy-квота)" = 1 ] && echo "$L" | grep -q "ГОТОВО gemini/г-agy-квота "'
N5=$(echo "$L" | grep -cE "ГОТОВО (gemini|claude)/(а-codex|б-codex|в-agy|д-claude|е-claude-gpu) ")
chk "решта п'яти — ГОТОВО (є: $N5)" '[ "$N5" = 5 ]'
echo "  кінці: $(echo "$L" | grep -v ПУЛИ | sed 's/GEMINI ОБГОРТКА: //' | sed -E 's/ [0-9a-f]{40}//' | tr '\n' ';')"

echo "=== Б: GPU — по одному на ноутбуці, замок спільний для gemini-run і claude-run"
setup b; export FAKE_ZERO_UNTIL=0; mark "gpu-agy/$AG/1/gpu"; mark "gpu-claude/$CC/1/gpu"
gem & cr & wait; gem & cr & wait
echo "  найбільше водночас GPU-нарядів: $(tl gpu); порядок: $(tl order)"
chk "дві GPU-позначки різних облікових записів — не водночас, обидві виконано" '[ "$(tl gpu)" = 1 ] && [ "$(grep -c "^start gpu" "$W/timeline.txt")" = 2 ]'

echo "=== В: N зі смуги.json на origin/main — 1, потім 2, без перевстановлення скриптів"
setup c; export FAKE_ZERO_UNTIL=0
(cd "$W/seed"; mkdir -p аудит/адаптери/gemini; lanes 1 2 2 > аудит/адаптери/gemini/смуги.json
 git add -A; git commit -q -m 'смуги 1'; git push -q origin main 2>/dev/null)
mark "n-codex-1/$CX/1"; mark "n-codex-2/$CX/1"; gem; A1=$(tl codex)
(cd "$W/seed"; lanes 2 2 2 > аудит/адаптери/gemini/смуги.json
 git commit -q -am 'смуги 2'; git push -q origin main 2>/dev/null)
: > "$W/timeline.txt"; mark "n-codex-3/$CX/1"; mark "n-codex-4/$CX/1"; gem; A2=$(tl codex)
(cd "$W/seed"; lanes 99 2 2 > аудит/адаптери/gemini/смуги.json; git commit -q -am 'смуги 99'; git push -q origin main 2>/dev/null)
git -C "$W/clone-g" fetch -q origin main 2>/dev/null
CE=$("$PW" -NoProfile -c ". '$(wp "$SRC/queue_lanes.ps1")'; \$RepoDir='$(wp "$W/clone-g")'; \$GitExe='git'; \$script:NoHooks='x'; function Write-Log {}; (Get-Limits).slots['codex']" 2>/dev/null | tr -d '\r')
echo "  codex водночас: смуги.json codex=1 → $A1, codex=2 → $A2; codex=99 у даних → $CE (стеля в коді)"
chk "N з файла даних міняє паралельність без перевстановлення (1 → 2)" '[ "$A1" = 1 ] && [ "$A2" = 2 ]'
chk "дані не перевищують стелі коду (99 → 64)" '[ "$CE" = 64 ]'

echo "=== Г: смуги.json задає 6 і 8 слотів, усі наряди справді працюють водночас"
for N in 6 8; do
  setup "slots-$N"; export FAKE_ZERO_UNTIL=0; export FAKE_HOLD=30
  (cd "$W/seed"; mkdir -p аудит/адаптери/gemini
   lanes "$N" 0 0 > аудит/адаптери/gemini/смуги.json
   for ((i=1; i<=N; i++)); do printf 'Т | наряд\n' > "аудит/наряди/n-codex-$i.md"; done
   git add -A; git commit -q -m "смуги $N"; git push -q origin main 2>/dev/null)
  for ((i=1; i<=N; i++)); do mark "n-codex-$i/$CX/1"; done
  gem
  ACTUAL=$(tl codex)
  chk "смуги.json codex=$N → $N водночас (є: $ACTUAL)" '[ "$ACTUAL" = "$N" ]'
  chk "усі $N нарядів закінчено" '[ "$(grep -c "^end " "$W/timeline.txt")" = "$N" ]'
done

echo; [ $BAD = 0 ] && echo "ВСЕ ✓" || echo "ЗБІЙ ✗"; exit $BAD
