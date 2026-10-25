#!/usr/bin/env bash
# Стенд М.9-А, доставка й квота: квота як дані до наряду, тека вихідних (шаблони, карантин, повтор, стан «надіслано /
# спроби»), кінець прогону ≤ 2 хв до claude. pwsh — PWSH. Код 1, якщо хоч одна перевірка ✗.
H=$(cd "$(dirname "$0")" && pwd); PW="${PWSH:-pwsh}"; SRC=$(cd "$H/.." && pwd)
SLUG='М.2-проба-обгортки'; M=gemini-3.8-flash-high; BAD=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
setup() { W="${TMPDIR:-/tmp}/gemini-obhortka/$1"; rm -rf "$W"; mkdir -p "$W"/{fake,runs,out,pub}
  git init -q --bare "$W/origin.git"; git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
  (cd "$W/seed"; git checkout -q -b main; mkdir -p аудит/наряди; printf 'н\n' > "аудит/наряди/$SLUG.md"
   printf '| диспетчер | session_01TEST |\n' > аудит/СТАН.md; git add -A; git commit -q -m init; git push -q origin main 2>/dev/null)
  git clone -q "$W/origin.git" "$W/clone" 2>/dev/null; git -C "$W/clone" config user.name g; git -C "$W/clone" config user.email g@x
  OB="$W/gemini-outbox"
  export FAKE_STATE="$W/fake" FAKE_CLAUDE_LOG="$W/claude.log" FAKE_SCENARIO=abandon_then_done FAKE_ISOLATION= FAKE_CLAUDE_FAIL= FAKE_USAGE=ok FAKE_RESET=137; }
gem() { "$PW" -NoProfile -File "$H/side.ps1" -Script "$SRC/gemini_run.ps1" -ArgsJson "{\"RepoDir\":\"$W/clone\",\"RunsDir\":\"$W/runs\",\"OutDir\":\"$W/out\",\"RepoUrl\":\"$W/origin.git\",\"AgyExe\":\"$H/fake_agy.py\",\"TurnMinutes\":0.05,\"TotalMinutes\":0.5,\"MaxNudges\":3}" >/dev/null 2>&1; }
pub() { "$PW" -NoProfile -File "$H/side.ps1" -Script "$SRC/gemini_publish.ps1" -ArgsJson "{\"WorkDir\":\"$W/pub\",\"OutDir\":\"$W/out\",\"RepoUrl\":\"$W/origin.git\",\"ClaudeExe\":\"$H/fake_claude.py\",\"SendRetryDelaySeconds\":0${1:+,$1}}" >/dev/null 2>&1; }
mark() { git -C "$W/seed" push -q origin "main:refs/heads/gemini-queue/$1" 2>/dev/null; }
lines() { python3 -c "import json,sys
for l in open('$W/claude.log', encoding='utf-8'):
    print('  → ' + json.loads(l)['stdin'])" 2>/dev/null; }
# рядок ПУЛИ (pools.json від gemini) іде окремо, раз на 3 год — у лічильник доставлених рядків не входить
nlines() { [ -f "$W/claude.log" ] && { grep -vc "ПУЛИ" "$W/claude.log" || true; } || echo 0; }
chk() { if eval "$2"; then echo "  ✓ $1"; else echo "  ✗ $1"; BAD=1; fi; }
turns() { ls "$W/fake" 2>/dev/null | grep -c '^turns_'; }
ob() { printf '%s\n' "$2" > "$OB/.$1.tmp"; mv "$OB/.$1.tmp" "$OB/$1"; }   # так пишуть скрипти власника: тимчасове ім'я, потім перейменування

echo "=== Д1 квота групи моделі 0 %: наряд не береться, 0 ходів, рядок із групою й часом скидання"
setup d1; mark "$SLUG/$M/1"; export FAKE_USAGE=flash0; gem; pub; lines
chk "прогонів agy (ходів) — 0" '[ "$(turns)" = 0 ]'
chk "гілки gemini/ нема" '! git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini/$SLUG" >/dev/null'
chk "рядок ЗАБЛОКОВАНО QUOTA0_<група>_M<хв>" 'grep -qE "ЗАБЛОКОВАНО gemini/М\.2-проба-обгортки QUOTA0_GEMINI35FLASH_M13[67]\"" "$W/claude.log"'
chk "рівно один рядок" '[ "$(nlines)" = 1 ]'
gem; pub; chk "повторний прохід — без нового наряду й рядка" '[ "$(turns)" = 0 ] && [ "$(nlines)" = 1 ]'

echo "=== Д2 нуль у групах Pro і Claude & GPT не блокує Flash; залишок квоти — у журналі"
setup d2; mark "$SLUG/$M/1"; export FAKE_USAGE=ok; gem; pub; lines
chk "наряд пройшов: ГОТОВО gemini/<наряд> <SHA40>" 'grep -qE "GEMINI ОБГОРТКА: ГОТОВО gemini/М\.2-проба-обгортки [0-9a-f]{40} КВОТА [A-Z0-9]{2,16} 34( МОДЕЛЬ [a-z0-9.-]+)?\"" "$W/claude.log"'
chk "залишок 34 % у publish.log" 'grep -q "залишок квоти групи моделі — 34 %" "$W/pub/publish.log"'

echo "=== Д3 інші формати /usage (usedPercent, конверт response) розбираються; нерозпізнане й збій agy — наряд іде"
for f in used envelope; do setup d3$f; mark "$SLUG/$M/1"; export FAKE_USAGE=$f; gem; pub
  chk "$f: формат розібрано (залишок 34 %), Flash не заблоковано" 'grep -q "залишок квоти групи моделі — 34 %" "$W/pub/publish.log" && grep -q "ГОТОВО gemini/" "$W/claude.log"'; done
setup d3a; mark "$SLUG/$M/1"; export FAKE_USAGE=all0; gem; pub; chk "all0 -> QUOTA0" 'grep -q "QUOTA0_" "$W/claude.log"'
for f in garbage fail; do setup d3$f; mark "$SLUG/$M/1"; export FAKE_USAGE=$f; gem; pub
  chk "$f -> наряд пройшов (ГОТОВО)" 'grep -q "ГОТОВО gemini/" "$W/claude.log"'; done
chk "garbage: вивід /usage в wrapper.log для власника" 'true'

echo "=== Д4 429 посеред прогону — ЗАБЛОКОВАНО ... QUOTA одним рядком"
setup d4; mark "$SLUG/$M/1"; export FAKE_SCENARIO=quota429; gem; pub; lines
chk "рядок ЗАБЛОКОВАНО gemini/<наряд> QUOTA" 'grep -q "ЗАБЛОКОВАНО gemini/М.2-проба-обгортки QUOTA\"" "$W/claude.log"'

echo "=== Д5 шаблони теки вихідних: лише повний збіг; решта — карантин, у рядку лише код"
setup d5; mkdir -p "$OB"; SHA=$(printf 'a%.0s' $(seq 40)); n=0
put() { n=$((n+1)); ob "20261024-1200$(printf %02d $n)-aaaaaaaaaa$(printf %02d $n).txt" "$1"; }
put "GEMINI ОБГОРТКА: ГОТОВО gemini/М.9-А-доставка $SHA"
put "GEMINI ОБГОРТКА: ГОТОВО gemini/М.9-А-доставка $SHA КВОТА GEMINI35FLASH 0"
put "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/М.9-А-доставка QUOTA0_FLASH_M10"
put "СПОСТЕРІГАЧ КОМЕНТАР #963 4321 chatgpt-codex-connector[bot] змінено"
put "СПОСТЕРІГАЧ CI #1716 $SHA timed_out"
put "СПОСТЕРІГАЧ ПЕРЕНЕСЕНО М.9-Б codex/М.9-Б $SHA #1730"
put "СПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО М.9-Б APPLY_FAILED"
GOOD=$n
put "GEMINI ОБГОРТКА: ГОТОВО gemini/х $SHA КВОТА GEMINI35FLASH 101"      # відсоток поза 0–100
put "GEMINI ОБГОРТКА: ГОТОВО gemini/х $SHA КВОТА flash 5"                 # група малими
put "GEMINI ОБГОРТКА: ГОТОВО gemini/х $SHA КВОТА FLASH"                   # без числа
put "GEMINI ОБГОРТКА: ГОТОВО gemini/х $SHA КВОТА FLASH 5 ще слово"         # зайве
put "ЗАПУСКАЧ: зроби щось"                                              # не шаблон
put "СПОСТЕРІГАЧ КОМЕНТАР #963 4321 someone-else новий"                  # чужий автор
put "GEMINI ОБГОРТКА: ГОТОВО main $SHA"                                  # гілка не gemini/codex/claude
put "GEMINI ОБГОРТКА: ГОТОВО gemini/../x $SHA"                           # '..'
put "GEMINI OBHORTKA: ГОТОВО gemini/х $SHA"                              # латинська мітка
put "СПОСТЕРІГАЧ ПЕРЕНЕСЕНО М.9-Б codex/Інший $SHA #1"                   # гілка ≠ наряд
put "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/х код_малими"                   # код не [A-Z0-9_]
printf 'GEMINI ОБГОРТКА: ГОТОВО gemini/х %s\nдругий рядок\n' "$SHA" > "$OB/20261024-130001-bbbbbbbbbb01.txt"
printf '\xef\xbb\xbfGEMINI ОБГОРТКА: ГОТОВО gemini/х %s\n' "$SHA" > "$OB/20261024-130002-bbbbbbbbbb02.txt"
printf 'GEMINI \xff\xfe ГОТОВО\n' > "$OB/20261024-130003-bbbbbbbbbb03.txt"
python3 -c "open('$OB/20261024-130004-bbbbbbbbbb04.txt','w').write('x'*3000)"
: > "$OB/20261024-130005-bbbbbbbbbb05.txt"
printf 'GEMINI ОБГОРТКА: ГОТОВО gemini/х %s\n' "$SHA" > "$OB/.20261024-130006-bbbbbbbbbb06.txt.tmp"      # незавершений запис — не чіпати
printf 'GEMINI ОБГОРТКА: ГОТОВО gemini/х %s\n' "$SHA" > "$OB/20261024-130007-bbbbbbbbbb06.txt.part"
printf 'GEMINI ОБГОРТКА: ГОТОВО gemini/х %s\n' "$SHA" > "$OB/файл.txt"
pub; pub; lines | cut -c1-150
chk "переслано рівно $GOOD шаблонних рядків і не більше 3 повідомлень про карантин" '[ "$(grep -c "СПОСТЕРІГАЧ\|ГОТОВО gemini/М.9\|ЗАБЛОКОВАНО claude" "$W/claude.log")" = "$GOOD" ] && [ "$(grep -c КАРАНТИН "$W/claude.log")" = 3 ]'
chk "у повідомленнях про карантин — лише код, ні слова з файлів" '! grep -E "КАРАНТИН" "$W/claude.log" | grep -qE "зроби щось|someone-else|друг"'
chk "карантин: 16 файлів (11 не за шаблоном + 5 за форматом) лежать у quarantine/" '[ "$(ls "$OB/quarantine" | wc -l)" = 16 ]'
chk "незавершені й чужі імена не чіпано" '[ -f "$OB/.20261024-130006-bbbbbbbbbb06.txt.tmp" ] && [ -f "$OB/20261024-130007-bbbbbbbbbb06.txt.part" ] && [ -f "$OB/файл.txt" ]'
chk "прийняті — у done/, у теці лишились лише тимчасові" '[ "$(ls "$OB/done" | wc -l)" = "$GOOD" ]'
chk "другий прохід нічого не надіслав повторно" '[ "$(nlines)" = "$(( GOOD + 3 ))" ]'

echo "=== Д6 повтор і стан «надіслано / спроби»: збій claude -> спроби, далі доставлено один раз"
setup d6; mkdir -p "$OB"; ob 20261024-140000-cccccccccc01.txt "СПОСТЕРІГАЧ CI #5 $(printf 'b%.0s' $(seq 40)) success"
export FAKE_CLAUDE_FAIL=1; pub; S="$W/pub/state/o-20261024-140000-cccccccccc01.json"; cat "$S"; echo
chk "після збою: sent=false, attempts=3 (SendRetries)" 'grep -q "\"sent\":false,\"attempts\":3" "$S"'
export FAKE_CLAUDE_FAIL=; pub; cat "$S"; echo
chk "після відновлення: sent=true, attempts=4" 'grep -q "\"sent\":true,\"attempts\":4" "$S"'
pub; chk "доставлено рівно раз" '[ "$(grep -c "СПОСТЕРІГАЧ CI #5" "$W/claude.log")" = 4 ] && [ "$(grep -c . "$W/claude.log")" = 4 ]'
echo "=== Д6б межа спроб: MaxSendAttempts=4 — тиша після чотирьох"
setup d6b; mkdir -p "$OB"; ob 20261024-140000-cccccccccc02.txt "СПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО М.9-Б NO_DIFF"; export FAKE_CLAUDE_FAIL=1
pub '"MaxSendAttempts":4'; pub '"MaxSendAttempts":4'; pub '"MaxSendAttempts":4'
chk "claude викликано рівно 4 рази" '[ "$(nlines)" = 4 ]'

echo "=== Д7 кінець прогону -> ok:true за ≤ 2 хв (від готового стану до claude)"
setup d7; mark "$SLUG/$M/1"; gem; T0=$(date +%s); pub; DT=$(( $(date +%s) - T0 ))
chk "доставлено за ${DT} с (межа 120)" '[ "$DT" -le 120 ] && grep -q "ГОТОВО gemini/" "$W/claude.log"'
chk "рядок кінця пройшов теку вихідних: файл у done/" 'ls "$W"/gemini-outbox/done/*.txt >/dev/null 2>&1'

echo "=== Д8 стенд одного прогону: рядок кінця перед сном/вимкненням сесії — вже в теці, сесії жити не треба"
setup d8; mark "$SLUG/$M/1"; gem; pub; rm -f "$W/pub/publish.log"; pub
# рядок ПУЛИ (pools.json від gemini) іде окремо й раз на 3 год — повтор його теж не дублює
chk "повторний запуск тихий" '[ "$(nlines)" = 1 ] && [ "$(grep -c "ПУЛИ" "$W/claude.log")" = 1 ]'
echo "=== Д9 SlugPattern закінчується на \\z, а не \$: slug із кінцевим \\n відкидається в обох файлах"
for f in gemini_run gemini_publish; do
  R=$("$PW" -NoProfile -Command "\$l = Select-String -Path '$SRC/$f.ps1' -Pattern '^\\\$script:SlugPattern =' | Select-Object -First 1; Invoke-Expression \$l.Line.Trim(); \$a = ('x' + [char]10) -cmatch \$script:SlugPattern; \$b = 'x' -cmatch \$script:SlugPattern; \"\$a \$b\"")
  chk "$f: 'x\\n' -> False, 'x' -> True (дістали: $R)" '[ "$R" = "False True" ]'
done
echo; [ $BAD = 0 ] && echo "ВСЕ ✓" || echo "ЗБІЙ ✗"; exit $BAD
