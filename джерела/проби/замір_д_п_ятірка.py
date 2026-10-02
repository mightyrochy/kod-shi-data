# -*- coding: utf-8 -*-
"""ЗАМІР-Д: казуальні за назвою речі у п'ятірці (запит вибору, руки 1–2) і в обраному образі; тека з <прогін>/вердикти.txt.gz. Нічого не викликає."""
import gzip, json, re, sys, glob
КАЗ = re.compile(r"кед|кросів|шльопан|в'єтнамк|шорти|худі|футболк|шопер|пляж|спортивн|толстовк|світшот|тапочк|сланц|угги|уги\b|джинс|бомбер|сабо|crocs", re.I)
дж = lambda с: json.loads(с[с.index("{"):]) if с and "{" in с else None
п5 = обр = 0
for f in sorted(glob.glob(sys.argv[1] + "/*/вердикти.txt.gz")):
    н = f.split("/")[-2]
    for в in json.load(gzip.open(f, "rt", encoding="utf-8"))["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        кл = в["етапи"]["виклики"]; ас = [дж(c["запит"]["текст"]) for c in кл if c["крок"] == "assembly"]; вб = [дж(c["запит"]["текст"]) for c in кл if c["крок"] == "choice"]
        if not ас or not вб or not ас[0] or not вб[-1]: print(н, "рука", в["рука"], "— нема ланцюга"); continue
        наз = {x["n"]: x["name"] for x in ас[0]["pool"]}
        for i, o in enumerate(вб[-1]["verdict"]):
            ск = [наз.get(x["n"], "")[:45] for x in o["your_outfit"]["items"] if КАЗ.search(наз.get(x["n"], ""))]
            if ск: п5 += 1; print(f"  п'ятірка · {н} р{в['рука']} · образ {i + 1}:", ск)
        сч = [x["назва"][:45] for x in в.get("речі_образу", []) if КАЗ.search(x["назва"])]; обр += bool(сч); сч and print(f"  ОБРАНО · {н} р{в['рука']}:", сч)
print("казуальних образів у п'ятірках:", п5, "· серед обраних:", обр)
