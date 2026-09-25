# локально (вирівнювання дужок після #329; копія rozkyd329.py + «врятовано вирівнюванням»): на кожен прогін стенда — виклики ремонту (скільки, скільки з невалідним JSON, вхідні
# токени проти контексту 61 440), описи (невалідний JSON), по руках 1–2 на вибір після ремонту: образів, без блокерів,
# зі взуттям, з її річчю; її річ у відповіді ремонту; картки (речей, сирий JSON у «Чому цей образ»); ✗ стенда.
# Запуск: rozkyd329.py <мітка> [<мітка> …]  (теки C:/tmp/vidpovidi25/<мітка> і C:/tmp/znimky25/<мітка>)
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8")
КОНТЕКСТ = 61440
def ч(т, ф):
    с = open(os.path.join(т, ф), encoding="utf-8").read(); п, _, в = с.partition("\n\n── ВІДПОВІДЬ")
    return п[п.index("\n") + 1:], (в[в.index("\n") + 1:] if "\n" in в else "")
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
def дж(т, строго=False, вирівнювати=False):
    м = re.search(r"```(?:json)?\s*([\s\S]*?)```", т or ""); т = (м.group(1) if м else т or "").strip()
    т = т[т.find("{"):т.rfind("}") + 1]
    try: return json.loads(т)
    except Exception:
        if вирівнювати:
            try: return json.loads(вирівняти(т))
            except Exception: pass
        return (None if строго else {})
нр = lambda р: р.get("н") if isinstance(р, dict) else р
норм = lambda р: (lambda м: "#%s·%s" % м.groups() if м else str(нр(р)))(re.match(r"\s*#\s*(\d+)\s*·\s*(\d+)", str(нр(р))))
for мітка in sys.argv[1:]:
    В, З = "C:/tmp/vidpovidi25/" + мітка, "C:/tmp/znimky25/" + мітка
    фф = sorted((x for x in os.listdir(В) if x.startswith("seed")), key=lambda x: int(x.split("_")[1]))
    пакети = [дж(ч(В, x)[0]) for x in фф if "ПАКЕТ_V1" in x]
    пули = [{р["н"] for рр in (п.get("пул") or {}).values() for р in рр} for п in пакети]
    закр = [set((п.get("обмеження") or {}).get("закріплені") or []) for п in пакети]
    рука = lambda нн: 1 + max(range(len(пули)), key=lambda і: len(set(нн) & пули[і]))
    рем = [x for x in фф if "ВЕРДИКТ_V1_ОБРАЗИ_V1" in x]
    погані = [x.split("_")[1] for x in рем if дж(ч(В, x)[1], строго=True) is None]
    лаг = [x for x in погані if дж(ч(В, [ф for ф in рем if ф.split("_")[1] == x][0])[1], строго=True, вирівнювати=True) is not None]
    скл = [x for x in фф if "ПАКЕТ_V1" in x]
    скл_п = [x.split("_")[1] for x in скл if дж(ч(В, x)[1], строго=True) is None]
    скл_л = [x for x in скл_п if дж(ч(В, [ф for ф in скл if ф.split("_")[1] == x][0])[1], строго=True, вирівнювати=True) is not None]
    описи = [x for x in фф if "ОПИС_V1" in x or ("інший" in x and "ОПИС_ВІДПОВІДЬ_V1" in ч(В, x)[0][:20000])]
    погані_о = [x.split("_")[1] for x in описи if дж(ч(В, x)[1], строго=True) is None]
    вик = json.load(open(З + "/модель_виклики.json", encoding="utf-8")); вик = вик if isinstance(вик, list) else (вик.get("виклики") or вик.get("calls") or [])
    ток = [(в.get("вхід") or 0, в.get("вихід") or 0) for в in вик if isinstance(в, dict) and в.get("тип") == "ВЕРДИКТ_V1→ОБРАЗИ_V1"]
    лог = open(З + "/прогін.log", encoding="utf-8").read(); рс = (len(re.findall(r"(?m)^  ✔", лог)), len(re.findall(r"(?m)^  ✗", лог)))
    print("\n######## %s · %s ✔ / %s ✗ · ✗ «лише прийнятий образ»: %s" % (мітка, рс[0], рс[1],
          "ТАК" if re.search(r"✗ на картку йде лише образ", лог) else "ні"))
    print("   ремонт: викликів %d · невалідний JSON %d (%s), з них вирівнювання лагодить %d · вхідних токенів: %s · найменший запас до 61 440: %s" % (len(рем), len(погані),
          ",".join(погані) or "—", len(лаг), " / ".join(str(а) for а, _ in ток), min((КОНТЕКСТ - а - б for а, б in ток), default="—")))
    print("   складання: викликів %d · невалідний JSON %d (%s), з них вирівнювання лагодить %d" % (len(скл), len(скл_п), ",".join(скл_п) or "—", len(скл_л)))
    н_оп = sum(1 for в in вик if isinstance(в, dict) and str(в.get("тип")).startswith("ОПИС_V1"))
    print("   опис: викликів %d (файлів %d) · невалідний JSON %d (%s)" % (н_оп, len(описи), len(погані_о), ",".join(погані_о) or "—"))
    перший = {}
    for x in рем:
        п, в = ч(В, x); вп = дж(п)
        суд = [с for с in (вп.get("вердикт") or []) if isinstance(с, dict)]
        if len(суд) < 2: continue
        р = рука([нр(р) for с in суд for р in (с.get("твій_образ") or {}).get("речі") or []])
        if р in перший: continue
        вв = дж(в, строго=True, вирівнювати=True)
        перший[р] = None if вв is None else [[норм(р_) for р_ in (о.get("речі") or [])] for о in (вв.get("образи") or []) if isinstance(о, dict)]
    картки = open(З + "/картки.txt", encoding="utf-8").read()
    for x in фф:
        if "ВЕРДИКТ_V1_ВИБІР_V1" not in x: continue
        оо = [с for с in (дж(ч(В, x)[0]).get("вердикт") or []) if isinstance(с, dict)]
        р = рука([нр(р_) for с in оо for р_ in (с.get("твій_образ") or {}).get("речі") or []])
        бл = [{б.get("код") for б in (с.get("структура") or {}).get("блокери") or []} for с in оо]
        її = sum(bool(закр[р - 1] & {нр(р_) for р_ in (с.get("твій_образ") or {}).get("речі") or []}) for с in оо)
        ра = перший.get(р, "нема")
        ра_т = "не розібрано" if ра is None else ("—" if ра == "нема" else "%d з %d" % (sum(bool(закр[р - 1] & set(о)) for о in ра), len(ра)))
        к = re.search(r"═══ картка \d з \d · рука %d · речей (\d+)[^\n]*\n([\s\S]*?)(?=═══ картка|\Z)" % р, картки)
        print("   рука %d · вибір: образів %d · без блокерів %d · зі взуттям %d · з її річчю %d · її річ у відповіді ремонту: %s · картка: %s речей%s" % (
              р, len(оо), sum(not б for б in бл), sum("нема_взуття" not in б for б in бл), її, ра_т, к.group(1) if к else "?",
              " · СИРИЙ JSON у «Чому цей образ»" if к and ("```json" in к.group(2) or '"версія"' in к.group(2)) else ""))
