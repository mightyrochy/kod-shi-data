# -*- coding: utf-8 -*-
"""5195: replay записаних ходів розмови (внутрішня мова й частини з файлів вердиктів стенда, без моделі) крізь
шов паспорта `мовний_шар.паспорт_з_шару`: втрати й вигадки полів, речення бульбашки не від моделі, повтори вже
показаних порад, коди й шматки коду на картці; і скільки конструкцій Б/В шляху паспорта (класифікація рядка 5195
над `шлях_слова_лічба.py`) ще стоїть. Запуск: cd джерела && python3 проби/паспорт_слова_5195.py [вердикти…]"""
import ast, collections, glob, gzip, json, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import мовний_шар as МШ, паспорт_нагоди as ПН
ПОЛЕ = dict({п: к for _, п, к in ПН.ПОЛЕ_ВИМІРУ if к}, formality="ошатність", hour="година", temperature_c="темп_c")
є, КОД = (lambda v: v not in (None, "", [], {}, "unknown", "невідомо")), re.compile(r"\b[a-z]+_[a-z_]+\b|\bunknown\b"); лік, бачено = collections.Counter(), set()
for ф in sorted(glob.glob("../аудит/**/verdykty*.json*", recursive=True) + glob.glob("../аудит/**/вердикти.txt*", recursive=True)) + sys.argv[1:]:
    try:
        d = json.load(gzip.open(ф, "rt", encoding="utf-8") if ф.endswith(".gz") else open(ф, encoding="utf-8"))
    except ValueError:
        continue
    ходи = [м for ч in (d.get("спільне") or {}).get("чат") or [] for м in ч.get("мова_шару") or []
            if м.get("напрям") == "turn" and isinstance(м.get("внутрішня"), dict)]
    ключ = json.dumps([(м.get("вхід"), м["внутрішня"], м.get("частини")) for м in ходи], ensure_ascii=False, sort_keys=True)
    if not ходи or ключ in бачено:
        continue
    бачено.add(ключ); лік["сцен"] += 1; п, слова = None, []
    for м in ходи:
        слова.append(str((м.get("вхід") or {}).get("слова") or "")); лік["ходів"] += 1; ч = м.get("частини") or {}
        р = МШ.паспорт_з_шару(м["внутрішня"], {}, паспорт_досі=п, слова_ходу=list(слова), частини=ч)
        до, п, в = п or {}, р["паспорт"], р["записано"]
        лік["втрати"] += sum(1 for к, x in в.items() if к in ПОЛЕ and є(x) and not є(п.get(ПОЛЕ[к])))
        лік.update("вигадка:" + пк for к, пк in ПОЛЕ.items() if є(п.get(пк)) and not є(до.get(пк)) and not є(в.get(к)))
        модель = " ".join(str(ч.get(к) or "") for к in ("text", "invite", "ask"))
        лік["речень_не_від_моделі"] += sum(1 for с in re.split(r"(?<=[.!?…])\s+", р.get("текст") or "") if с.strip() not in модель)
        лік["повтори_порад"] += len(set(р.get("теми_поради") or ()) & {МШ._ВМ.код("advice_topic", т) for т in до.get("поради_дані") or ()})
        шматки = ПН.паспорт_шматками_людині(п)
        лік.update("шматок_коду:" + ш["ключ"] for ш in шматки if ш.get("текст") and ш.get("ключ") != "подія")
        лік["кодів_на_екрані"] += len(КОД.findall((р.get("текст") or "") + " " + " · ".join(ш.get("текст") or "" for ш in шматки)))
print("ПІДСУМОК: " + " · ".join("%s %d" % кв for кв in sorted(лік.items())))
БВ = {"паспорт_нагоди": ("ВЕТО_СЛОВА", "_ЖІНЦІ_ЗАЙМЕННИКИ", "_ЖІНЦІ_ТВІЙ", "_ЖІНЦІ_ВАШ", "_ЖІНЦІ_ДІЄСЛОВА", "СІМʼЇ_НАГОД_ПІДПИСИ",
      "_НЕВІДОМО_СИНОНІМИ"), "profile": ("_СЛОВА_РЕЧІ", "СЕНСОРНІ"), "сценарій": ("_ОПАДИ_СИНОНІМИ",), "brief": ("ТЕМА_ЗА_КОДОМ",)}
лишились = [ц.id for м, імена in БВ.items() for в in ast.parse(open(м + ".py", encoding="utf-8").read()).body
            if isinstance(в, ast.Assign) for ц in в.targets if isinstance(ц, ast.Name) and ц.id in імена
            and not (ц.id == "СЕНСОРНІ" and isinstance(в.value.elts[0].elts[0], ast.Constant))]   # ключ-код, не кортеж слів
print("Б/В шляху паспорта: %d із %d · лишились: %s" % (len(лишились), sum(map(len, БВ.values())), ", ".join(лишились)))
