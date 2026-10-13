# -*- coding: utf-8 -*-
"""П-3: латиниця на картках — до/після на сирих відповідях перекладачки з прогону Н-1 (26.09, MamayLM).

Кожен виклик шару над текстами картки (`seed3_*_мовний_шар.txt`) іде через `мовний_шар.прийняти` ДО
(суворий розбір, як на main) і ПІСЛЯ (дочитування форми, П-3). Друкує: скільки текстів шар не повернув,
скільки латинських літер лягло б на картку («°C» — одиниця, не рахується) і які ключі показ шле в шар ще
раз (без відповіді або сама латиниця — `лишеЛатиницеюП`); що й після повтору лишилось самою латиницею,
на картку не лягає. Першими — картки прогону, як їх зняв стенд (`kartky_n1.txt`).
Свій прогін: `python3 проби/мова_картки_рук34.py <тека VIDPOVIDI стенда або .tar.gz>`."""
import os, re, sys, json, tarfile
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, К)
import мовний_шар as М
СИРІ = os.path.join(К, "..", "аудит", "тести", "сирі_2026-09-26")
лат = lambda т: len(re.findall(r"[A-Za-z]", re.sub(r"°[CF]", "", т)))
лише_лат = lambda т: bool(re.search(r"[^\W\d_]", т)) and not re.search(r"[^\W\d_A-Za-z]", т)
def до(розм, від):          # main: суворий розбір — без дочитування екрана й вхідної форми
    з = М._екрани, М._з_форми
    М._екрани, М._з_форми = (lambda т: т), (lambda x: (None, None))
    try: return М.прийняти(розм, від)
    finally: М._екрани, М._з_форми = з
def сирі(ш):                 # тека VIDPOVIDI стенда або архів сирих відповідей
    if os.path.isdir(ш): return [(ф, open(os.path.join(ш, ф), encoding="utf-8").read()) for ф in sorted(os.listdir(ш))]
    with tarfile.open(ш) as т_: return [(ч.name, т_.extractfile(ч).read().decode("utf-8")) for ч in т_ if ч.isfile()]
if len(sys.argv) < 2:
    for б in open(os.path.join(СИРІ, "kartky_n1.txt"), encoding="utf-8").read().split("═══ картка")[1:]:
        print("на знімку 26.09: картка%s· латиниці %d" % ("·".join(б.split("·")[:2]), лат(б.split("═══", 1)[1])))
for імя, с in sorted(сирі(sys.argv[1] if len(sys.argv) > 1 else os.path.join(СИРІ, "vidpovidi_n1_kontsert_gemma_s3.tar.gz"))):
    if "мовний_шар" not in імя or "── ВІДПОВІДЬ" not in с: continue
    пр, від = с.split("── ВІДПОВІДЬ")[0], с.split("── ВІДПОВІДЬ")[1].split("──\n", 1)[1].strip()
    if "ТЕКСТИ:" not in пр: continue
    розм = М.розмітити({str(т["н"]): т["текст"] for т in json.loads(пр[пр.index("ТЕКСТИ:") + 7:])})
    а, б = до(розм, від), М.прийняти(розм, від)
    повтор = [к for к in б["тексти"] if к in б["без_відповіді"] or лише_лат(б["тексти"][к])]
    лишено = [v for к, v in б["тексти"].items() if к not in повтор]
    слова = sorted({с for v in лишено for с in re.findall(r"\S*[A-Za-z]\S*", re.sub(r"°[CF]", "", v))})
    print("%s · текстів %2d │ ДО: без відповіді %d, латиниці %3d │ ПІСЛЯ: без відповіді %d, латиниці %d%s"
          " │ у шар ще раз: %s%s" % (імя.split("/")[-1][:8], len(розм), len(а["без_відповіді"]),
                                    sum(лат(v) for v in а["тексти"].values()), len(б["без_відповіді"]),
                                    sum(лат(v) for v in лишено), (" (" + " ".join(слова) + ")") if слова else "",
                                    ",".join(повтор) or "—", ("; " + "; ".join(б["нотатки"])) if б["нотатки"] else ""))
