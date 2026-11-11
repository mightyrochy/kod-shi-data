#!/usr/bin/env bash
# Незалежна проба рядка 14488: лише локальний origin і заглушки; аргумент — тека перевірка обгортки.
# JSON і marker-state підробляються разом; після трьох публікацій повертається справжній результат.
H="$1"; . "$H/середовище.sh"; PW="${PWSH:-pwsh}"; SRC=$(cd "$H/.." && pwd)
SLUG='М.2-проба-обгортки'; M=gemini-3.8-flash-high; BAD=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
setup() { W=$(mktemp -d "${TMPDIR:-/tmp}/3463-forged-XXXXXX"); mkdir -p "$W"/{fake,runs,out,pub}
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
has() { git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini-queue/$1" 2>/dev/null; }
runs() { grep -cE 'наряд .*->' "$W/runs/wrapper.log" 2>/dev/null; }
# Зняття диспетчером: коміт «ЗНЯТО…» поверх позначки (видаляти гілку він не може).
zn() { O=$(has "$1"); C=$(git -C "$W/seed" commit-tree "$O^{tree}" -p "$O" -m "ЗНЯТО: $2"); git -C "$W/seed" push -q origin "$C:refs/heads/gemini-queue/$1" 2>/dev/null; }
ok() { if eval "$2"; then echo "  ✓ $1"; else BAD=1; echo "  ✗ $1"; fi; }
setup forged-both; mark "$SLUG/$M/1"; gem
mkdir -p "$W/held"; J=$(ls "$W"/out/2*.json | head -1); mv "$J" "$W/held/"
MK=$(has "$SLUG/$M/1"); S=$(grep -l '^DONE ' "$W"/out/marker-state/*.txt | head -1)
cp "$S" "$W/held/state.txt"
printf '{"v":1,"id":"20000101-000000-aaaaaaaaaaaa","slug":"%s","model":"%s","n":1,"marker":"%s","start":"","head":"","code":"NO_REPORT","report":"NONE","ahead":0,"turns":1,"minutes":0,"bundle":""}' "$SLUG" "$M" "$MK" > "$W/out/20000101-000000-aaaaaaaaaaaa.json"
printf 'DONE 20000101-000000-aaaaaaaaaaaa NO_REPORT' > "$S"
pub; pub; pub
if [ -n "$(has "$SLUG/$M/1")" ]; then echo 'ПОЗНАЧКА_ПІСЛЯ_ПІДРОБКИ=є'; else echo 'ПОЗНАЧКА_ПІСЛЯ_ПІДРОБКИ=нема'; fi
cp "$W/held/state.txt" "$S"; mv "$W/held/$(basename "$J")" "$W/out/"; pub
if git -C "$W/origin.git" rev-parse -q --verify "refs/heads/gemini/$SLUG" >/dev/null; then echo 'СПРАВЖНІЙ_РЕЗУЛЬТАТ=опубліковано'; else echo 'СПРАВЖНІЙ_РЕЗУЛЬТАТ=втрачено'; fi
grep -E 'знято —|не відповідає жодній позначці' "$W/pub/publish.log" || true