#!/bin/bash
# $1 = до|після ; сцени: ж4_робота (ж4), ж1_свято_тріада (портрет ж7), ж8_зима-палітра (ж8)
R=/home/user/kod-shi-data
P=$(uv python find 3.12.1)
if [ ! -s /tmp/очі-до/index.html ]; then
  (cd /tmp/main/джерела && LYUSTERKO_PYC_PYTHON=$P LYUSTERKO_CATALOG=повний python3 build_артефакт.py . /tmp/очі-до/index.html показ-повний > /tmp/очі-прогін/збірка-до.log 2>&1)
fi
run(){ # вид id жінка портрет текст
  local V=$1 ID=$2 ZH=$3 PT=$4 TXT=$5; local OUT=/tmp/очі-прогін/$V/$ID; rm -rf $OUT; mkdir -p $OUT/знімки $OUT/відповіді
  local STOR=/tmp/очі; [ $V = до ] && STOR=/tmp/очі-до
  local TREE=$R; [ $V = до ] && TREE=/tmp/main
  echo "старт $(date -u +%FT%TZ)" > $OUT/час.txt
  (cd $TREE && DO=palitra OTSINKA=0 FOTO=0 CHAT_TEXT="$TXT" ZHINKA=$R/аудит/проби/жінки/$ZH.json PORTRET=$R/аудит/проби/набір-фото-жінок/$PT-портрет.jpg \
    ZHYVA=sonnet VIDPOVIDI=$OUT/відповіді ZNIMKY=$OUT/знімки ZVIT_OUT=$OUT/вердикти.txt CHROMIUM=/opt/pw-browsers/chromium \
    timeout 2400 node аудит/проби/рв6_стенд.js http://127.0.0.1:8765 $STOR /tmp/pyodide 3 > $OUT/лог.txt 2>&1)
  echo "rc=$? кінець $(date -u +%FT%TZ)" >> $OUT/час.txt
}
for V in "$@"; do
  run $V ж4_робота ж4 ж4 "робочий день в офісі" &
  run $V ж1_свято_тріада ж7 ж7 "хочу яскравий образ на свято, схема палітри — тріада" &
  run $V ж8_зима ж8 ж8 "на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин" &
  wait
done
echo ГОТОВО
