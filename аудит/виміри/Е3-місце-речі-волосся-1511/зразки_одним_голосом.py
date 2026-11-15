# Рішення менеджера 15.11 (15478): зразки одного волосся у фікстурі — один голос у формі виміру портрета
# (покоординатна медіана Lab, як `портрет_вимір` зводить пікселі ділянки). Запуск з кореня:
# python3 -X utf8 аудит/виміри/Е3-місце-речі-волосся-1511/зразки_одним_голосом.py [--записати]
import sys, os, json, glob
sys.path.insert(0, "джерела")
import colorspace as cs, міст_вхід as МВ
РІЗНІ_ПАСМА = {"ж1_дві_половини.json"}  # задумана з різними пасмами — лишається з кількома голосами
for ш in sorted(glob.glob("аудит/проби/жінки/*.json")):
    ім = os.path.basename(ш); ж = json.load(open(ш, encoding="utf8")); h = ж["hair"]
    if ім in РІЗНІ_ПАСМА or len(h) < 2:
        print(ім, h, "— лишається"); continue
    один = cs.hex_з_lab(МВ.медіана_lab([cs.hx(x) for x in h]))
    print(ім, h, "→", [один])
    if "--записати" in sys.argv:
        сирий = open(ш, encoding="utf8").read()
        старе = json.dumps(h, ensure_ascii=False)
        assert сирий.count(старе) == 1, (ім, старе)
        open(ш, "w", encoding="utf8").write(сирий.replace(старе, json.dumps([один])))
