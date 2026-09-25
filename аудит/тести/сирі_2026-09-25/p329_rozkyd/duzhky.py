# локально: скільки невалідних відповідей складання/ремонту лагодить вирівнювання дужок (закривна не та — ставимо ту,
# що чекає стек; рядки JSON не чіпаємо). Лише вимір — у продукт нічого не йде.
import os, re, json, sys
sys.stdout.reconfigure(encoding="utf-8")
def тіло(в):
    м = re.search(r"```(?:json)?\s*([\s\S]*?)```", в or ""); т = (м.group(1) if м else в or "").strip()
    return т[т.find("{"):т.rfind("}") + 1] if "{" in т else т
def вирівняти(т):
    вих, стек, у_рядку, екран = [], [], False, False
    for с in т:
        if у_рядку:
            вих.append(с)
            if екран: екран = False
            elif с == "\\": екран = True
            elif с == '"': у_рядку = False
            continue
        if с == '"': у_рядку = True
        elif с in "{[": стек.append("}" if с == "{" else "]")
        elif с in "}]":
            if not стек: continue
            с = стек.pop()
        вих.append(с)
    return "".join(вих) + "".join(reversed(стек))
корінь = r"C:\tmp\vidpovidi25"; всього = полаг = 0
for n in sorted(os.listdir(корінь)):
    if not n.startswith(("kvar01_0b730bf", "kv2_f5745d7", "p326_0a192e9", "b315b_", "mff6_ir", "p329_ir", "mfa3_ir")): continue
    for ф in sorted(os.listdir(os.path.join(корінь, n))):
        if "ПАКЕТ_V1_ОБРАЗИ_V1" not in ф and "ВЕРДИКТ_V1_ОБРАЗИ_V1" not in ф: continue
        с = open(os.path.join(корінь, n, ф), encoding="utf-8").read(); в = с.partition("\n\n── ВІДПОВІДЬ")[2]; в = в[в.index("\n") + 1:] if "\n" in в else ""
        т = тіло(в)
        try: json.loads(т); continue
        except Exception: pass
        всього += 1
        try: д = json.loads(вирівняти(т)); полаг += 1; стан = "лагодиться: образів %d" % len(д.get("образи") or [])
        except Exception as е: стан = "ні (%s)" % str(е)[:60]
        print("%-22s %-10s %s" % (n, ф[:9], стан))
print("невалідних %d · вирівнювання дужок лагодить %d" % (всього, полаг))
