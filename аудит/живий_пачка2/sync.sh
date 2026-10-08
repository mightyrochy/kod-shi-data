#!/bin/bash
# синхронізує out/ → гілку, коміт+пуш при зміні; до 2 год
W=/c/tmp/zhp2/wtr; D=$W/аудит/живий_пачка2; END=$(( $(date +%s) + 7200 ))
cd $W
while [ $(date +%s) -lt $END ]; do
  mkdir -p $D
  for E in ДО ПІСЛЯ; do [ -d /c/tmp/zhp2/out/$E ] && { mkdir -p $D/$E; cp -r /c/tmp/zhp2/out/$E/. $D/$E/; }; done
  cp /c/tmp/zhp2/{run.sh,proksi.log} $D/ 2>/dev/null
  git add аудит/живий_пачка2 >/dev/null 2>&1
  if ! git diff --cached --quiet; then
    git commit -qm "живий-пачка2: прогін (проміжно) $(tail -qn1 /c/tmp/zhp2/out/*/done.txt 2>/dev/null | tr '\n' ' ')" && GIT_NO_LAZY_FETCH=1 git push --no-thin -q -u origin claude/zhyvyi-pachka-2 2>&1 | tail -1
  fi
  grep -q ALLDONE /c/tmp/zhp2/out/ПІСЛЯ/done.txt 2>/dev/null && break
  sleep 600
done
