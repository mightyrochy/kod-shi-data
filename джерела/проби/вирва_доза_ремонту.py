# -*- coding: utf-8 -*-
"""ВИРВА-СМІЛИВІСТЬ (рядки 841, 886): що `вердикт_моделі.сміливі_набору` дав би ремонтові 10→5 на ЗАПИСАНИХ промптах.
Нічого не викликає. Аргументи: тека з <прогін>/вердикти.txt.gz (типово аудит/перевірки/vyrva_968) і фільтр імені теки.
Друкує на руку: намір, сміливі образи кодом (ід:ознаки), дозу «лишити», скільки з них ремонт ДО справді лишив, і чи доза
була б виконана ДО. Річ дроту → опис коду: type→слот (`СЛОТ_ТИПУ`), fabric/shine/pattern/color/hex — ті самі поля."""
import gzip, json, glob, re, sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import внутрішня_мова as В, вердикт_моделі as ВМ
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../аудит/перевірки/vyrva_968")
Ф = re.compile(sys.argv[2] if len(sys.argv) > 2 else ".")
дж = lambda с: (json.loads(с) if с and с.lstrip()[:1] == "{" else None)
def опис(i):  # річ дроту → (слот ядра, опис з ключами `_річ_пулу`)
    сл = В.ТАБЛИЦЯ["slot"].get(В.СЛОТ_ТИПУ.get(i.get("type") or "", ""))
    return сл, {"тканина": i.get("fabric"), "блиск": i.get("shine"), "візерунок": i.get("pattern"), "колір": i.get("color"), "hex": i.get("hex")}
РАЗОМ = dict(рук=0, з_дозою=0, сміливих=0, лишено=0, доза_ДО=0)
for f in sorted(x for x in glob.glob(Т + "/*/вердикти.txt.gz") if Ф.search(x.split("/")[-2])):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        for c in в["етапи"]["виклики"]:
            if c["крок"] != "repair":
                continue
            п, відп = дж(c["запит"]["текст"]), дж(c["відповідь_сира"])
            if not (п and відп):
                continue
            case = п["case"] if isinstance(п.get("case"), dict) else {  # «case» рядком (до ВИРВА-968): намір зі слів мети
                "intent": "statement" if "Мета: експресія" in str(п.get("case")) else None, "goal": "express"}
            зап = [(o["your_outfit"]["id"], dict(речі_н=[i["n"] for i in o["your_outfit"]["items"]],
                                                  описи_н={i["n"]: опис(i)[1] for i in o["your_outfit"]["items"]},
                                                  слоти_н={i["n"]: опис(i)[0] for i in o["your_outfit"]["items"]})) for o in п["verdict"]]
            смл = ВМ.сміливі_набору(зап, намір=case.get("intent"), мета=case.get("goal"), варіантів=п.get("outfits_wanted"))
            лиш = {o["id"] for o in відп.get("outfits") or []}
            сі = [x["ід"] for x in (смл or {}).get("образи", [])]
            РАЗОМ["рук"] += 1; РАЗОМ["з_дозою"] += bool(смл); РАЗОМ["сміливих"] += len(сі); РАЗОМ["лишено"] += len(set(сі) & лиш)
            РАЗОМ["доза_ДО"] += bool(смл) and len(set(сі) & лиш) >= смл["лишити"]
            print(f.split("/")[-2], в["рука"], case.get("intent") or "—", "| сміливі:", ", ".join("%s:%s" % (x["ід"], "+".join(x["ознаки"])) for x in (смл or {}).get("образи", [])) or "—",
                  "| лишити", (смл or {}).get("лишити", "—"), "| ремонт ДО лишив", len(set(сі) & лиш), "з", len(сі))
print("разом:", РАЗОМ)
