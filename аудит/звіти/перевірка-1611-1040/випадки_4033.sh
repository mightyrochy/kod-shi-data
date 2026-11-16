#!/bin/bash
# Власні випадки перевірки #4033: клон голови, core.hooksPath як у SessionStart, кожен випадок — з чистого стану.
# Для кожного: «зупинено» (HEAD не зрушив) чи «пройшло»; поруч — що сказав би старий хук main (JSON PreToolUse).
# Виклик: випадки_4033.sh <клон> <добрий.md> <хибний.md> <старий_хук.py>
K="$1"; D="$2"; X="$3"; ST="$4"
F=аудит/дошка/claude/т.md
cd "$K" || exit 2
BASE=$(git rev-parse HEAD)
скинути() { git reset -q --hard "$BASE"; git clean -qfd аудит/дошка; }
старий() {  # $1 — команда; друкує deny/пропуск
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.stdin.read()},"cwd":sys.argv[1]}))' "$K" \
    | CLAUDE_PROJECT_DIR="$K" python3 "$ST" 2>/dev/null | grep -q '"deny"' && echo відмова || echo пропуск
}
випадок() {  # $1 назва, $2 підготовка (bash), $3 команда коміту (bash)
  скинути; eval "$2"
  s0=$(старий "$3")
  pre=$(git rev-parse HEAD)
  (eval "$3") >/tmp/пер/вивід 2>&1
  post=$(git rev-parse HEAD)
  [ "$pre" = "$post" ] && res=зупинено || res=пройшло
  printf '%-58s новий: %-9s старий: %s\n' "$1" "$res" "$s0"
  [ "$res" = зупинено ] && grep -m1 -E 'ПОМИЛКА|ЗАСТЕРЕЖЕННЯ|error|fatal' /tmp/пер/вивід | cut -c1-150 | sed 's/^/      /'
}
for V in хибний добрий; do
  [ $V = хибний ] && F1="$X" || F1="$D"
  echo "== файл $V"
  випадок "1 add && commit -m" "cp $F1 $F" "git add $F && git commit -q -m x"
  випадок "2 commit -am (файл уже в HEAD)" "sed s/16991/16993/ $D > $F; git add $F; git commit -q --no-verify -m база; cp $F1 $F" "git commit -q -am x"
  випадок "3 --amend" "echo z > z.txt; git add z.txt; git commit -q -m перший; cp $F1 $F; git add $F" "git commit -q --amend --no-edit"
  випадок "4 cd в підтеку" "cp $F1 $F" "cd аудит/дошка && git add claude/т.md && git commit -q -m x"
  випадок "5 git -C з іншої теки" "cp $F1 $F" "cd /tmp && git -C '$K' add $F && git -C '$K' commit -q -m x"
  випадок "6 коментар оболонки (форма 15933)" "cp $F1 $F" $'# крок 3: коміт\ngit add -A  # усе\ngit commit -q -m x'
  випадок "7 sh -c" "cp $F1 $F" "sh -c 'git add $F && git commit -q -m x'"
  випадок "8 commit -F - heredoc з апострофом (15931б)" "cp $F1 $F; git add $F" $'git commit -q -F - <<\'EOF\'\nпам\'ять\nEOF'
  випадок "9 commit -- <шлях> (без add, файл новий у індексі)" "cp $D $F; git add $F; cp $F1 $F" "git commit -q -m x -- $F"
  випадок "10 git worktree (друге дерево)" "git worktree remove -f /tmp/пер/дерево2 2>/dev/null; git worktree add -q -f /tmp/пер/дерево2 HEAD; cp $F1 /tmp/пер/дерево2/$F" "cd /tmp/пер/дерево2 && git add $F && git commit -q -m x"
done
echo "== індекс і робоче дерево розходяться"
випадок "11 індекс хибний, дерево добре" "cp $X $F; git add $F; cp $D $F" "git commit -q -m x"
випадок "12 індекс добрий, дерево хибне" "cp $D $F; git add $F; cp $X $F" "git commit -q -m x"
скинути; git worktree remove -f /tmp/пер/дерево2 2>/dev/null
