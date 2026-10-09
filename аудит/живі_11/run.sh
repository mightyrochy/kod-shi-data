#!/bin/bash
# $1 = файл сцен. Збірка: C:/tmp/zh11/site (код 0196e33b), проксі :1236 (qwen 57344, MamayLM 16384).
export PATH="$PATH:/c/Users/Admin/.lmstudio/.internal/utils:/c/Users/Admin/.lmstudio/bin"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NODE_PATH=C:/Users/Admin/kod-shi-test-node/node_modules
SHA=0196e33b81967d8cbf92569d8f46e8489e7e3ea7; T=/c/tmp/zh11; R=/c/tmp/zh0810/R; REPO=/c/Users/Admin/kod-shi-data
BR=claude/zhyvi-pislia-11; SITE=$T/site; ET=ПІСЛЯ
export MODEL_URL=http://127.0.0.1:1236/v1 MODEL=qwen/qwen3.5-9b MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 FOTO=1
while IFS='|' read -r ID WJ TXT X; do
  [ -z "$ID" ] && continue
  D=$T/out/$ID; OUT=$REPO/аудит/живі_11/$ID
  for TRY in 1 2; do
    rm -rf $D; mkdir -p $D
    export ZNIMKY=$D/знімки ZVIT_OUT=$D/вердикти.txt VIDPOVIDI=$D/VIDPOVIDI ZHINKA=$R/$WJ.json CHAT_TEXT="$TXT"
    for kv in $X; do export "$kv"; done
    S=$(date +%s)
    ( cd $REPO && timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $SITE C:/tmp/pyodide 3 > $D/лог.txt 2>&1 )
    RC=$?; SEC=$(( $(date +%s) - S ))
    for kv in $X; do unset ${kv%%=*}; done
    [ $RC -le 1 ] && break
    cp $D/лог.txt $T/out/${ID}_лог_$TRY.txt
    echo "$ID спроба $TRY rc=$RC ${SEC}с — збій середовища" >> $T/out/done.txt
  done
  rm -rf $OUT; mkdir -p $OUT; cp -r $D/. $OUT/; cp $T/out/${ID}_лог_1.txt $OUT/лог_1.txt 2>/dev/null
  case $ID in Н4) RID=ж1_оціни_образ_6б;; К7) RID=ж7_мороз_без_відкритого;; Н3) RID=ж7_корпоратив_директор;; Н1) RID=ж1_ювілей_свекрухи_2хід;; *) RID=$ID;; esac
  echo "$SHA $RID $ET $MODEL+$MODEL_MOVA" > $OUT/код.txt
  echo "$ID rc=$RC ${SEC}с $(date +%T)" >> $T/out/done.txt; cp $T/out/done.txt $REPO/аудит/живі_11/done.txt; cp $T/proksi.log $REPO/аудит/живі_11/proksi.log 2>/dev/null
  ( cd $REPO && git add аудит/живі_11 >/dev/null 2>&1 && git commit -qm "живі-11: $ET $ID rc=$RC ${SEC}с

Co-Authored-By: Claude Code <noreply@anthropic.com>" )
  for i in 1 2 3 4; do ( cd $REPO && GIT_NO_LAZY_FETCH=1 git push --no-thin -q -u origin $BR ) && break; sleep $((2<<i)); done
done < <(tr -d '\r' < $1)
echo ALLDONE >> $T/out/done.txt
