import json, sys, collections
Д = json.load(open(sys.argv[1])); П = json.load(open(sys.argv[2]))
print("записів", Д["записів"], П["записів"], "ювелірних", len(Д["записи"]), len(П["записи"]), "сек", Д["секунд"], П["секунд"])
спільні = [к for к in Д["записи"] if к in П["записи"]]
ДЗ, ПЗ = Д["записи"], П["записи"]
з_мет = [к for к in спільні if ДЗ[к]["метал"]]
print("з кодом металу", len(з_мет), "без", len(спільні) - len(з_мет))
for поле in ("частка", "тон_кадру", "вставки", "хром_вставка", "спір", "меж", "колір_металу", "невідомий", "несе", "нейтраль_невідома"):
    def кл(v):
        if поле == "частка" and isinstance(v, (int, float)):
            return "0" if v == 0 else ">0"
        return v
    for група, кк in (("з металом", з_мет), ("без металу", [к for к in спільні if not ДЗ[к]["метал"]])):
        п = collections.Counter((кл(ДЗ[к][поле]), кл(ПЗ[к][поле])) for к in кк)
        зм = {f"{a}→{b}": n for (a, b), n in п.items() if a != b}
        ДО = collections.Counter(кл(ДЗ[к][поле]) for к in кк); ПІ = collections.Counter(кл(ПЗ[к][поле]) for к in кк)
        print(f"  {поле} [{група}]: ДО {dict(ДО)} ПІСЛЯ {dict(ПІ)} змін {sum(зм.values())} {зм}")
print("палітри метал:", collections.Counter(p["метал"] for p in Д["палітри"]), collections.Counter(p["метал"] for p in П["палітри"]))
