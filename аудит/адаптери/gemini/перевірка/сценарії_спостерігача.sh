#!/usr/bin/env bash
# Стенд спостерігача М.9-Б без Windows (pwsh 7, git, python3): локальний «origin», підробний gh (fake_gh.py).
# 9 сценаріїв: базова лінія, коментарі, CI, перенос, відмови переносу, ворожі назви, збій gh, ліміт рядків, формат теки.
# Кожен рядок теки перевіряється за шаблонами наряду. pwsh — змінна PWSH.
H=$(cd "$(dirname "$0")" && pwd); PW="${PWSH:-pwsh}"; SRC=$(cd "$H/.." && pwd)
SLUG='М.9-проба-спостерігача'; R=mightyrochy/kod-shi-data; BOT='chatgpt-codex-connector[bot]'
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@x GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@x
ts() { date -u -d "$1 sec" +%Y-%m-%dT%H:%M:%SZ; }
sha() { python3 -c "import hashlib,sys;print(hashlib.sha1(sys.argv[1].encode()).hexdigest())" "$1"; }
setup() { W="${TMPDIR:-/tmp}/gemini-watch/$1"; rm -rf "$W"; mkdir -p "$W"/{fake,out,work}
  git init -q --bare "$W/origin.git"; git clone -q "$W/origin.git" "$W/seed" 2>/dev/null
  (cd "$W/seed"; git checkout -q -b main; printf 'один\nдва\nтри\n' > a.txt; mkdir -p аудит/адаптери/gemini; echo w > аудит/адаптери/gemini/w.txt
   git add -A; git commit -q -m init; git push -q origin main 2>/dev/null
   git checkout -q -b "codex/$SLUG"; git commit -q --allow-empty -m "наряд"; git push -q origin "codex/$SLUG" 2>/dev/null)
  HEAD0=$(git -C "$W/origin.git" rev-parse "refs/heads/codex/$SLUG"); export FAKE_GH_DIR="$W/fake" FAKE_GH_FAIL=
  pulls "[1801,mightyrochy,$HEAD0,codex/$SLUG]"; checks "$HEAD0" completed success
  patches; }
pulls() { python3 - "$FAKE_GH_DIR/pulls.json" "$@" <<'P'
import json,sys
out=[]
for a in sys.argv[2:]:
    n,u,s,r,*f=a.strip('[]').split(',')
    out.append({"number":int(n),"user":{"login":u},"head":{"sha":s,"ref":r,"repo":{"full_name":f[0] if f else "mightyrochy/kod-shi-data"}}})
json.dump(out,open(sys.argv[1],'w'))
P
}
checks() { python3 - "$FAKE_GH_DIR/checks_$1.json" "${@:2}" <<'P'
import json,sys
a=sys.argv[2:]; json.dump([{"status":a[i],"conclusion":a[i+1] or None} for i in range(0,len(a),2)],open(sys.argv[1],'w'))
P
}
# cmt <N> <id> <login> <відступ секунд для updated_at> [файл тіла]
cmt() { python3 - "$FAKE_GH_DIR/comments_$1.json" "$2" "$3" "$(ts "$4")" "${5:-}" <<'P'
import json,os,sys
p,i,l,t,b=sys.argv[1:]
c=json.load(open(p)) if os.path.exists(p) else []
body=open(b,encoding='utf-8').read() if b else 'текст'
c=[x for x in c if x['id']!=int(i)]+[{"id":int(i),"user":{"login":l},"created_at":t,"updated_at":t,"body":body}]
json.dump(c,open(p,'w'),ensure_ascii=False)
P
}
body() { printf 'Ось diff:\n\n```diff\n' > "$1"; cat "$2" >> "$1"; printf '```\n' >> "$1"; }
patches() { P="$W/patch"; mkdir -p "$P"
  printf 'diff --git a/a.txt b/a.txt\n--- a/a.txt\n+++ b/a.txt\n@@ -1,3 +1,3 @@\n один\n-два\n+2\n три\ndiff --git a/нове.txt b/нове.txt\nnew file mode 100644\n--- /dev/null\n+++ b/нове.txt\n@@ -0,0 +1 @@\n+новий\n' > "$P/ok.diff"
  sed 's/-два/-чотири/' "$P/ok.diff" > "$P/bad.diff"
  sed 's/+2$/+з\xef\xbf\xbd/' "$P/ok.diff" > "$P/fffd.diff"
  printf 'diff --git a/.github/workflows/w.yml b/.github/workflows/w.yml\nnew file mode 100644\n--- /dev/null\n+++ b/.github/workflows/w.yml\n@@ -0,0 +1 @@\n+x\n' > "$P/gh.diff"
  printf 'diff --git a/аудит/адаптери/gemini/zz.ps1 b/аудит/адаптери/gemini/zz.ps1\nnew file mode 100644\n--- /dev/null\n+++ b/аудит/адаптери/gemini/zz.ps1\n@@ -0,0 +1 @@\n+x\n' > "$P/wr.diff"
  printf 'diff --git a/b.bin b/b.bin\nnew file mode 100644\nindex 0000000..e69de29\nGIT binary patch\nliteral 0\nHcmV?d00001\n\n' > "$P/bin.diff"
  printf 'diff --git a/l b/l\nnew file mode 120000\nindex 0000000..1111111\n--- /dev/null\n+++ b/l\n@@ -0,0 +1 @@\n+a.txt\n\\ No newline at end of file\n' > "$P/link.diff"
  printf 'diff --git a/.git/hooks/x b/.git/hooks/x\nnew file mode 100644\n--- /dev/null\n+++ b/.git/hooks/x\n@@ -0,0 +1 @@\n+x\n' > "$P/dotgit.diff"
  printf 'diff --git a/../ззовні b/../ззовні\nnew file mode 100644\n--- /dev/null\n+++ b/../ззовні\n@@ -0,0 +1 @@\n+x\n' > "$P/outside.diff"; }
watch() { "$PW" -NoProfile -File "$SRC/gemini_watch.ps1" -WorkDir "$W/work" -OutDir "$W/out" -Repo "$R" -RepoUrl "$W/origin.git" \
  -GhExe "$H/fake_gh.py" "$@"; echo "  код виходу: $?" >&2; }
rows() { for f in $(ls "$W/out" | grep -v '\.part$' | sort); do cat "$W/out/$f"; echo; done | sed '/^$/d'; }
n() { ls "$W/out" 2>/dev/null | grep -c '\.txt$'; }
mv_out() { mkdir -p "$W/seen"; mv "$W/out"/*.txt "$W/seen/" 2>/dev/null; }
# Прогін і показ нових рядків: ім'я -> рядки, що з'явились від минулого показу.
step() { watch "${@:2}" 2>/dev/null; echo "-- $1: рядків $(n)"; rows | sed 's/^/   /'; mv_out; }
check_format() { python3 - "$W" <<'P'
import os,re,sys,glob
w=sys.argv[1]; sl=r'[\w][\w._-]{0,79}'; sh=r'[0-9a-f]{40}'
T=[r'СПОСТЕРІГАЧ КОМЕНТАР #\d+ \d+ (mightyrochy|chatgpt-codex-connector\[bot\]) (новий|змінено)',
   r'СПОСТЕРІГАЧ CI #\d+ %s (success|failure|cancelled|timed_out|action_required|neutral|skipped|pending)'%sh,
   r'СПОСТЕРІГАЧ ПЕРЕНЕСЕНО %s codex/%s %s #\d+'%(sl,sl,sh), r'СПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО %s [A-Z0-9_]{2,40}'%sl]
bad=0; tot=0
for d in ('out','seen'):
    for f in glob.glob(os.path.join(w,d,'*')):
        b=open(f,'rb').read(); tot+=1
        ok=re.fullmatch(r'\d{8}-\d{6}-[0-9a-f]{12}\.txt',os.path.basename(f)) and not b.startswith(b'\xef\xbb\xbf') and b'\n' not in b and any(re.fullmatch(t,b.decode()) for t in T)
        if not ok: bad+=1; print('  ✗ формат:',os.path.basename(f),b[:80])
print('  %s формат усіх %d файлів: ім\'я, UTF-8 без BOM, один рядок, шаблон'%('✓' if not bad else '✗',tot)); 
P
}
echo "=== 1 базова лінія: перший прохід мовчить, другий теж"; setup w1
cmt 963 100 mightyrochy -3600; cmt 1801 101 "$BOT" -3600; checks "$HEAD0" completed failure
step "прохід 1"; step "прохід 2"; ls "$W/work/state.json" >/dev/null && echo "  ✓ стан записано"
echo "=== 2 коментарі: новий, змінено, чужі не йдуть, повтор мовчить"; setup w2; step "базова лінія"
cmt 963 200 mightyrochy -60; cmt 963 201 stranger -60; cmt 963 202 mightyrochy2 -60; cmt 963 203 MightyRochy -60
cmt 1801 210 "$BOT" -60; cmt 1801 211 "gemini-code-assist[bot]" -60; step "нові"; step "повтор"
sleep 1; cmt 963 200 mightyrochy 0; cmt 1801 210 "$BOT" 0; step "правка двох"; step "після правки"
echo "=== 3 CI: pending мовчить, зміна стану йде, чужі PR ні, закритий зникає"; setup w3
pulls "[1801,mightyrochy,$HEAD0,codex/$SLUG]" "[1802,mightyrochy,$(sha a),claude/x]" "[1803,stranger,$(sha b),claude/y]" "[1804,mightyrochy,$(sha c),claude/z,other/fork]"
checks "$(sha a)" completed success; step "базова лінія"
checks "$(sha a)" in_progress ""; checks "$(sha c)" completed failure; step "pending (рядків 0)"
checks "$(sha a)" completed success completed failure; checks "$(sha b)" completed failure; step "failure поверх success"
checks "$(sha a)" completed failure completed failure; step "без змін"
pulls "[1801,mightyrochy,$HEAD0,codex/$SLUG]" "[1802,mightyrochy,$(sha d),claude/x]"; checks "$(sha d)" completed cancelled completed success; step "нова голова, cancelled"
checks "$(sha d)"; step "нема перевірок -> pending"; pulls "[1801,mightyrochy,$HEAD0,codex/$SLUG]"; step "1802 закрито"
grep -c '"i:1802"' "$W/work/state.json" | sed 's/^/  1802 у стані: /'
echo "=== 4 перенос: diff лягає -> гілка codex/<наряд>, рядок, без повтору"; setup w4; step "базова лінія"
body "$W/b.md" "$W/patch/ok.diff"; cmt 1801 400 "$BOT" -30 "$W/b.md"; step "відповідь бота"
OUT=$(git -C "$W/origin.git" rev-parse "refs/heads/codex/$SLUG"); echo "  гілка: $([ "$OUT" != "$HEAD0" ] && echo пересунута || echo '✗ не змінилась')"
git -C "$W/origin.git" show "$OUT:a.txt" | tr '\n' '|'; echo; git -C "$W/origin.git" show "$OUT:нове.txt"
git -C "$W/origin.git" log --format='  коміт: %s' -1 "$OUT"; git -C "$W/origin.git" for-each-ref --format='  ref %(refname)' | tr '\n' ' '; echo
step "повтор"; echo "  main недоторканий: $(git -C "$W/origin.git" show main:a.txt | tr '\n' '|')"
echo "=== 5 відмови переносу: код причини, гілка не рухається"; setup w5; step "базова лінія"
i=500; for c in bad fffd gh wr bin link dotgit outside; do i=$((i+1)); body "$W/b.md" "$W/patch/$c.diff"; cmt 1801 $i "$BOT" -30 "$W/b.md"; done
step "вісім поганих diff"; body "$W/b.md" "$W/patch/ok.diff"; cmt 1801 590 mightyrochy -20 "$W/b.md"; cmt 1801 591 stranger -20 "$W/b.md"; step "diff від не-бота: лише коментар власника"
[ "$(git -C "$W/origin.git" rev-parse "refs/heads/codex/$SLUG")" = "$HEAD0" ] && echo "  ✓ гілка codex/$SLUG не рухалась" || echo "  ✗ гілка рухалась"
printf 'Це лише відповідь без diff\n' > "$W/b.md"; cmt 1801 592 "$BOT" -10 "$W/b.md"; step "відповідь бота без diff: лише коментар"
body "$W/b.md" "$W/patch/ok.diff"; sleep 1; cmt 1801 501 "$BOT" 0 "$W/b.md"; step "правка bad -> ok: переноситься"
body "$W/b.md" "$W/patch/ok.diff"; cmt 1801 593 "$BOT" 1 "$W/b.md"; step "TOO_BIG" -MaxDiffKB 0
echo "=== 6 ворожі назви гілок і PR: нічого, крім шаблонів"; setup w6; step "базова лінія"
pulls "[1801,mightyrochy,$HEAD0,codex/$SLUG]" "[1810,mightyrochy,$(sha e),codex/..evil]" "[1811,mightyrochy,$(sha f),codex/a b]" "[1812,mightyrochy,$(sha g),codex/x;rm]" "[1813,stranger,$(sha h),codex/chuzha]"
python3 - "$FAKE_GH_DIR/pulls.json" <<'P'
import json,sys
p=json.load(open(sys.argv[1])); p.append({"number":1814,"user":{"login":"mightyrochy"},"head":{"sha":"a"*40,"ref":"codex/nl\n","repo":{"full_name":"mightyrochy/kod-shi-data"}}}); json.dump(p,open(sys.argv[1],'w'))
P
body "$W/b.md" "$W/patch/ok.diff"; for N in 1810 1811 1812 1813 1814; do cmt $N 60$N "$BOT" -20 "$W/b.md"; done
for c in e f g h; do checks "$(sha $c)" completed success; done; checks "$(printf 'a%.0s' $(seq 40))" completed success
step "п'ять ворожих PR"
echo "=== 7 збій gh: код 1, рядків нема, стан не просунувся, далі наздоганяє"; setup w7; step "базова лінія"; cmt 963 700 mightyrochy -20
export FAKE_GH_FAIL=1; watch 2>&1 | grep -q "код виходу: 1" && echo "  ✓ gh не відповідає -> код виходу 1" || echo "  ✗ код виходу не 1"; echo "  рядків: $(n)"; export FAKE_GH_FAIL=; step "gh знову працює"
echo "=== 8 ліміт рядків: 5 нових коментарів при MaxRows 2 -> 3 проходи, без дублів"; setup w8; step "базова лінія"
for i in 1 2 3 4 5; do cmt 963 80$i mightyrochy -30; done; step "прохід 1" -MaxRows 2; step "прохід 2" -MaxRows 2; step "прохід 3" -MaxRows 2; step "прохід 4" -MaxRows 2
echo "=== 9 формат теки вихідних для всього, що було у w2..w8"
for s in w2 w3 w4 w5 w6 w7 w8; do W="${TMPDIR:-/tmp}/gemini-watch/$s"; printf '  %s: ' $s; check_format | tail -1; done
