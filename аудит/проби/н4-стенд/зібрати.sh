#!/bin/bash
# Сцени стенда Н4 у звіт: картка сценарію (знімок 390×844), перша картка руки 1, картка ядра даними, звірка запитів.
# $1 — тека прогонів (/tmp/n4/прогін); сцени — решта аргументів. Імена змінних латиницею: bash кириличних не має.
P=$1; shift; T=$(dirname "$0")
for s in "$@"; do
  mkdir -p $T/$s; z=$P/$s/знімки
  cp $z/scenarii_knopka_nad_panelliu_seed3.png $T/$s/картка_сценарію.png 2>/dev/null
  cp $z/n4_kartka_stsenariiu.json $T/$s/картка_ядра.json 2>/dev/null
  i=$(python3 -c "import json;k=json.load(open('$P/$s/стан.json')).get('картки') or [];print(next((n for n,x in enumerate(k) if x.get('рука')==1),''))" 2>/dev/null)
  [ -n "$i" ] && cp $z/n3_kartka_${i}_390x844.png $T/$s/рука1.png
  python3 $T/звірка.py $P/$s > $T/$s/звірка.txt 2>&1
  cp $P/$s/час.txt $T/$s/
  grep -h "✗\|СТИЛІСТКА МОВЧИТЬ\|ЖИВА МОДЕЛЬ" $P/$s/лог.txt | cut -c1-300 > $T/$s/лог_коротко.txt
done
