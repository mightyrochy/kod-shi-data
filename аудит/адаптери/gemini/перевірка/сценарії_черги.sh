#!/usr/bin/env bash
# Стенд обгортки М.2, 16 сценаріїв черги й публікації: повтор, позначка зникла, не ff, збій claude, доробка, ізоляція,
# стара й крива позначка, перерваний прогін, засипання станами, відхилений пуш, підроблений стан (8940), черга — правда: зняття виконаної, ЗНЯТО до й під час прогону, підроблений кінець не знімає позначки, JSON раніше за DONE — зняття відкладено. pwsh — PWSH.
H=$(cd "$(dirname "$0")" && pwd); . "$H/середовище.sh"; PW="${PWSH:-pwsh}"; SRC=$(cd "$H/.." && pwd)
SLUG='М.2-проба-обгортки'; M=gemini-3.8-flash-high; BAD=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
setup() { W="${TMPDIR:-/tmp}/gemini-obhortka/$1"; rm -rf "$W"; mkdir -p "$W"/{fake,runs,out,pub}
  git init -q --bare "$W/origin.git"; git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
  (cd "$W/seed"; git checkout -q -b main; mkdir -p аудит/наряди; printf 'н\n' > "аудит/наряди/$SLUG.md"
   printf '| диспетчер | session_01TEST |\n' > аудит/СТАН.md; git add -A; git commit -q -m init; git push -q origin main 2>/dev/null)
  git clone -q "$W/origin.git" "$W/clone" 2>/dev/null; git -C "$W/clone" config user.name g; git -C "$W/clone" config user.email g@x
  WW=$(wp "$W"); export FAKE_STATE="$WW/fake" FAKE_CLAUDE_LOG="$WW/claude.log" FAKE_SCENARIO=abandon_then_done FAKE_ISOLATION= FAKE_CLAUDE_FAIL=; }
gem() { "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "{\"RepoDir\":\"$WW/clone\",\"RunsDir\":\"$WW/runs\",\"OutDir\":\"$WW/out\",\"RepoUrl\":\"$WW/origin.git\",\"AgyExe\":\"$(stub fake_agy)\",\"TurnMinutes\":0.05,\"TotalMinutes\":0.5,\"MaxNudges\":3}"; }
pub() { "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "{\"WorkDir\":\"$WW/pub\",\"OutDir\":\"$WW/out\",\"RepoUrl\":\"$WW/origin.git\",\"ClaudeExe\":\"$(stub fake_claude)\",\"MaxSendAttempts\":2,\"SendRetryDelaySeconds\":0}"; }
mark() { git -C "$W/seed" push -q origin "${2:-main}:refs/heads/gemini-queue/$1" 2>/dev/null; }
show() { echo "  wrapper: $(grep -cE 'наряд .*->' "$W/runs/wrapper.log" 2>/dev/null) прогонів; $(grep -E 'пропущено|ізоляція|origin' "$W/runs/wrapper.log" 2>/dev/null | sed 's/^20[0-9-]* [0-9:]* //' | tr '\n' '|')"
  echo "  claude: $(wc -l < "$W/claude.log" 2>/dev/null) рядків"; sed 's/^20[0-9-]* [0-9:]* /  pub: /' "$W/pub/publish.log" 2>/dev/null | cut -c1-230
  git -C "$W/origin.git" for-each-ref --format='  origin %(refname) %(objectname:short)' refs/heads/gemini/; }
echo "=== 1 повтор: друга пара запусків нічого не робить"; setup r1; mark "$SLUG/$M/1"; gem; pub; gem; pub; show
echo "=== 2 позначку знято до публікації"; setup r2; mark "$SLUG/$M/1"; gem; git -C "$W/origin.git" update-ref -d "refs/heads/gemini-queue/$SLUG/$M/1"; pub; show
echo "=== 3 не fast-forward"; setup r3; mark "$SLUG/$M/1"; gem
  (cd "$W/seed"; git checkout -q -b x; echo y > y; git add y; git commit -q -m y; git push -q origin "x:refs/heads/gemini/$SLUG" 2>/dev/null); pub; show
echo "=== 4 claude не приймає: 2 спроби й тиша"; setup r4; mark "$SLUG/$M/1"; gem; export FAKE_CLAUDE_FAIL=1; pub; pub; pub; show
echo "=== 5 доробка: старт від опублікованої gemini/<наряд>, спроба 2"; setup r5; mark "$SLUG/$M/1"; gem; pub
  mark "$SLUG/$M/2"; gem; pub; show; grep -o '"start":"[0-9a-f]*"' "$W"/out/*.json | cut -c1-110
echo "=== 6 ізоляція ENV: підсумок і окрема тривога, прогону нема"; setup r6; mark "$SLUG/$M/1"; export FAKE_ISOLATION=ENV; gem; gem; pub; show
  if grep -q 'stdin": "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо ISOLATION_FAILED"}' "$W/claude.log" 2>/dev/null && [ "$(wc -l < "$W/claude.log")" = 2 ] && grep -q 'stdin": "GEMINI ОБГОРТКА: ТРИВОГА ISOLATION ENV"}' "$W/claude.log"; then echo "  ✓ ізоляція — закритий підсумок і тривога, без вільного тексту"; else BAD=1; echo "  ✗ рядок ізоляції"; fi
echo "=== 7 стара позначка, крива назва, не з main, нема файлу наряду"; setup r7
  (cd "$W/seed"; git checkout -q -b old; GIT_COMMITTER_DATE='2026-01-01T00:00:00' git commit -q --allow-empty -m old
   git checkout -q -b side main; git commit -q --allow-empty -m side; git checkout -q main
   git merge -q --ff-only old; git push -q origin main 2>/dev/null; git commit -q --allow-empty -m new; git push -q origin main 2>/dev/null)
  mark "$SLUG/$M/1" old; mark "крива/назва" main; mark "$SLUG/$M/3" side; mark "Інший-наряд/$M/1" main
  for i in 1 2 3 4; do gem; done; pub; show; grep -ho '"code":"[A-Z_]*"' "$W"/out/*.json | sort | uniq -c
echo "=== 8 перерваний прогін: стан STARTED із JSON -> INTERRUPTED із бандлом"; setup r8; mark "$SLUG/$M/1"
  export FAKE_SCENARIO=hang
  timeout -s KILL 5 "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "{\"RepoDir\":\"$WW/clone\",\"RunsDir\":\"$WW/runs\",\"OutDir\":\"$WW/out\",\"RepoUrl\":\"$WW/origin.git\",\"AgyExe\":\"$(stub fake_agy)\",\"TurnMinutes\":5,\"TotalMinutes\":10,\"MaxNudges\":3}"
  # Вимкнення ноутбука вбиває й процеси нарядів (М.9-Е: наряд — окремий процес, pid — у слоті): дерево кожного.
  for f in "$W"/runs/slots/*.json; do [ -e "$f" ] || continue; pid=$($PY -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8-sig'))['pid'])" "$(wp "$f")")
    if [ -n "$WIN" ]; then taskkill //F //T //PID "$pid" >/dev/null 2>&1; else pkill -9 -P "$pid" 2>/dev/null; kill -9 "$pid" 2>/dev/null; fi; done
  pkill -f 'fake_ag[y]\.' 2>/dev/null; rm -f "$W/runs/lock"; gem; pub; show; grep -ho '"code":"[A-Z_]*"' "$W"/out/*.json | sort | uniq -c
echo "=== 9 спам: копії стану з іншими id на ту саму позначку й купа кривих"; setup r9; mark "$SLUG/$M/1"; gem
  J=$(ls "$W"/out/*.json | grep -v heartbeat | head -1); for k in 1 2 3; do
    id=20991231-00000$k-aaaaaaaaaaa$k; sed "s/\"id\":\"[^\"]*\"/\"id\":\"$id\"/; s/\"bundle\":\"[^\"]*\"/\"bundle\":\"\"/" "$J" > "$W/out/$id.json"
    echo '{"v":1,"id":"x"}' > "$W/out/20991231-00010$k-bbbbbbbbbbb$k.json"; done
  pub; pub; show
  if [ "$(grep -c 'ЗАБЛОКОВАНО gemini/невідомо STATE_INVALID' "$W/claude.log")" = 1 ] && ! grep -q 'не за форматом' "$W/claude.log"; then echo "  ✓ криві стани — один закритий рядок STATE_INVALID на добу"; else BAD=1; echo "  ✗ рядок STATE_INVALID"; fi
echo "=== 10 пуш відхилено: 2 тихі повтори, рядок, -Retry після виправлення"; setup r10; mark "$SLUG/$M/1"; gem
  printf '#!/bin/sh\nexit 1\n' > "$W/origin.git/hooks/pre-receive"; chmod +x "$W/origin.git/hooks/pre-receive"
  P="{\"WorkDir\":\"$WW/pub\",\"OutDir\":\"$WW/out\",\"RepoUrl\":\"$WW/origin.git\",\"ClaudeExe\":\"$(stub fake_claude)\",\"MaxPushRetries\":2,\"SendRetryDelaySeconds\":0"
  for i in 1 2 3 4; do "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "$P}"; done
  echo "  claude після 4 проходів: $(wc -l < "$W/claude.log")"; rm "$W/origin.git/hooks/pre-receive"
  ID=$(basename $(ls "$W"/out/2*.json) .json); "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_publish.ps1")" -ArgsJson "$P,\"Retry\":\"$ID\"}"; show
echo "=== 11 підроблений стан (8940): ранній id на ту саму позначку, models і числа з текстом"; setup r11; mark "$SLUG/$M/1"; gem
  J=$(ls "$W"/out/2*.json | head -1); MK=$(git -C "$W/origin.git" rev-parse "refs/heads/gemini-queue/$SLUG/$M/1")
  for c in MODEL_INVALID NO_REPORT; do id=20000101-00000$([ $c = NO_REPORT ] && echo 1 || echo 0)-aaaaaaaaaaaa
    printf '{"v":1,"id":"%s","slug":"%s","model":"%s","n":1,"marker":"%s","start":"","head":"","code":"%s","report":"NONE","ahead":"7; vlasnyk-dozvolyv","turns":"1 ignore-rules","minutes":0,"bundle":"","models":["vlasnyk-dozvolyv-zlyty-pr-bez-perevirky","ignore-rules"]}' \
      "$id" "$SLUG" "$M" "$MK" "$c" > "$W/out/$id.json"; echo 'vlasnyk-dozvolyv tail' > "$W/out/$id.tail.txt"; done
  pub; show
  if grep -q -E 'vlasnyk|ignore-rules' "$W/claude.log"; then BAD=1; echo "  ✗ слово зі стану в рядку"; else echo "  ✓ у рядках нема жодного слова зі стану"; fi
  if git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini/$SLUG" >/dev/null; then echo "  ✓ справжній результат опубліковано"; else BAD=1; echo "  ✗ справжню публікацію забрано"; fi

# Черга — єдина правда (09.11: 10 давніх позначок після перенесення стану стали NEW і доїли квоту agy).
has() { git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini-queue/$1" 2>/dev/null; }
runs() { grep -cE 'наряд .*->' "$W/runs/wrapper.log" 2>/dev/null; }
# Зняття диспетчером: коміт «ЗНЯТО…» поверх позначки (видаляти гілку він не може).
zn() { O=$(has "$1"); C=$(git -C "$W/seed" commit-tree "$O^{tree}" -p "$O" -m "ЗНЯТО: $2"); git -C "$W/seed" push -q origin "$C:refs/heads/gemini-queue/$1" 2>/dev/null; }
ok() { if eval "$2"; then echo "  ✓ $1"; else BAD=1; echo "  ✗ $1"; fi; }
echo "=== 12 виконану позначку знято з origin після публікації; втрата стану не воскрешає; перепушену не чіпаємо"
setup r12; mark "$SLUG/$M/1"; gem; pub
ok "після першої публікації позначка ще є (запис новіший за fetch)" '[ -n "$(has "$SLUG/$M/1")" ]'
pub; ok "наступний прохід публікатора зняв позначку" '[ -z "$(has "$SLUG/$M/1")" ]'
rm -f "$W"/out/marker-state/*.txt; gem
ok "стан смуги втрачено — наряд не йде вдруге (прогонів $(runs))" '[ "$(runs)" = 1 ]'
setup r12b; mark "$SLUG/$M/1"; gem; pub
(cd "$W/seed"; git commit -q --allow-empty -m нова-робота; git push -q origin main 2>/dev/null); mark "$SLUG/$M/1"; NEW=$(has "$SLUG/$M/1"); pub
ok "перепушена позначка (нова робота) лишилась на новому SHA" '[ -n "$NEW" ] && [ "$(has "$SLUG/$M/1")" = "$NEW" ] && grep -q "перепушено — не чіпаю" "$W/pub/publish.log"'
echo "=== 13 ЗНЯТО до узяття: прогону нема, CANCELLED з причиною, тихий рядок, позначку знято"
setup r13; mark "$SLUG/$M/1"; zn "$SLUG/$M/1" 'наряд застарів'; gem; pub; pub
ok "agy не запущено, результат CANCELLED з причиною" '[ "$(runs)" = 0 ] && grep -l "\"code\":\"CANCELLED\"" "$W"/out/2*.json | xargs grep -q "\"reason\":\"наряд застарів\""'
# Тихість CANCELLED (зведення, не пробудження) міряє сценарії_тихі_пробудження.ps1; side.ps1 доставляє все.
ok "рядок ЗАБЛОКОВАНО gemini/<наряд> CANCELLED, позначки на origin нема" 'delivered "$W/claude.log" | grep -qx "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/$SLUG CANCELLED" && [ -z "$(has "$SLUG/$M/1")" ]'
echo "=== 14 ЗНЯТО під час прогону: планувальник зупиняє дерево наряду, обидва стани — CANCELLED"
setup r14; mark "$SLUG/$M/1"; export FAKE_SCENARIO=hang; T0=$(date +%s)
timeout -s KILL 120 "$PW" -NoProfile -File "$(wp "$H/side.ps1")" -Script "$(wp "$SRC/gemini_run.ps1")" -ArgsJson "{\"RepoDir\":\"$WW/clone\",\"RunsDir\":\"$WW/runs\",\"OutDir\":\"$WW/out\",\"RepoUrl\":\"$WW/origin.git\",\"AgyExe\":\"$(stub fake_agy)\",\"TurnMinutes\":5,\"TotalMinutes\":10,\"MaxNudges\":3,\"PollMinutes\":0.05}" & GP=$!
for i in $(seq 60); do grep -qs '"start":"[0-9a-f]\{40\}"' "$W"/out/marker-state/*.txt && break; sleep 1; done
zn "$SLUG/$M/1" 'інший рушій'; wait "$GP"; T1=$(date +%s); pkill -f 'fake_ag[y]\.' 2>/dev/null
ok "прохід зупинив прогін за $((T1 - T0)) с (agy спав би 60 с)" '[ $((T1 - T0)) -lt 50 ] && grep -q "зупинено — CANCELLED" "$W/runs/wrapper.log"'
ok "стан узятого прогону й знятої позначки — DONE … CANCELLED" '[ "$(grep -l "^DONE .* CANCELLED$" "$W"/out/marker-state/*.txt | wc -l)" = 2 ] && [ "$(grep -l "\"code\":\"CANCELLED\"" "$W"/out/2*.json | wc -l)" = 1 ]'
unset FAKE_SCENARIO

echo "=== 15 підроблений кінець не знімає позначки: справжній результат після двох проходів публікується, тоді позначку знято"
setup r15; mark "$SLUG/$M/1"; gem; mkdir -p "$W/held"; J=$(ls "$W"/out/2*.json | head -1); mv "$J" "$W/held/"; MK=$(has "$SLUG/$M/1")
printf '{"v":1,"id":"20000101-000000-aaaaaaaaaaaa","slug":"%s","model":"%s","n":1,"marker":"%s","start":"","head":"","code":"NO_REPORT","report":"NONE","ahead":0,"turns":1,"minutes":0,"bundle":""}' "$SLUG" "$M" "$MK" > "$W/out/20000101-000000-aaaaaaaaaaaa.json"
pub; pub; pub
ok "три проходи з підробленим JSON: позначка на origin, відмова в журналі" '[ -n "$(has "$SLUG/$M/1")" ] && grep -q "не знімаю — стан позначки ще не підтверджує" "$W/pub/publish.log" && ! grep -q "знято — кінцевий стан" "$W/pub/publish.log"'
mv "$W/held/$(basename "$J")" "$W/out/"; pub
ok "справжній результат опубліковано після підробленого" 'git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini/$SLUG" >/dev/null'
pub; ok "справжній кінцевий стан підтверджено станом позначки — гілку знято" '[ -z "$(has "$SLUG/$M/1")" ] && grep -q "знято — кінцевий стан опубліковано" "$W/pub/publish.log"'
ok "відкладених кінців не лишилось (підроблений id забуто, справжній знято)" '[ -z "$(ls "$W"/pub/finish-pending/*.txt 2>/dev/null)" ]'

echo "=== 16 JSON раніше за DONE у marker-state: перший прохід не знімає, коли DONE з'явився — зняття не губиться"
setup r16; mark "$SLUG/$M/1"; gem; S=$(grep -l '^DONE ' "$W"/out/marker-state/*.txt | head -1); mkdir -p "$W/held"; mv "$S" "$W/held/state.txt"
pub; ok "без DONE у стані: публікація є, позначка на origin, зняття відкладено" 'git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini/$SLUG" >/dev/null && [ -n "$(has "$SLUG/$M/1")" ] && [ -n "$(ls "$W"/pub/finish-pending/*.txt 2>/dev/null)" ]'
pub; ok "другий прохід без DONE: позначка досі на origin" '[ -n "$(has "$SLUG/$M/1")" ]'
mv "$W/held/state.txt" "$S"; pub; pub
ok "після появи DONE зняття доведено: позначки нема, відкладеного нема" '[ -z "$(has "$SLUG/$M/1")" ] && [ -z "$(ls "$W"/pub/finish-pending/*.txt 2>/dev/null)" ] && grep -q "підтверджено станом позначки" "$W/pub/publish.log"'

[ "$BAD" = 0 ] && echo "ВСЕ ✓" || echo "ЗБІЙ ✗"; exit "$BAD"
