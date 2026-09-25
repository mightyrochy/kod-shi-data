"""П.6 наряду 25.09, роль ВХІД: чи правильно модель перекладає слова жінки в поля паспорта. Промпт — функцією продукту
`паспорт_нагоди.промпт_паспорта` з типовою формою сторінки (11:00, 18 °C, решта порожня), розбір — `паспорт_з_json`.
Друкує на кожну фразу: що дала модель (сире) і що з цього взяв код; оцінку «правильно / вигадала / пропустила» ставить
людина очима. Відповіді цілком — у теку ВИХІД. Запуск (з теки джерела):
MODEL_URL=http://127.0.0.1:1234/v1 MODELS=м1,м2 [PROMPT=короткий] python ../аудит/проби/мова_вхід.py <тека ВИХІД>
PROMPT=короткий — не промпт продукту, а стислий (поля без переліку ключів і правил): відділяє модель від промпта."""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding="utf-8")
import паспорт_нагоди as ПН
ФРАЗИ = ["гуляю з собаками в парку, вітер, яскраво хочу одягатись, по-дівчачому, ніжний і зручний образ у світлих тонах, у мене є світлі джинси кльош",
         "робочий день в офісі, дрес-код business casual, без підборів", "смужку? ні, клітинку хочу", "хочу смужку",
         "люблю смужку. ні", "не хочу темні", "ні в якому разі", "куртку чи жакет, не темного кольору",
         "не ношу куртки, краще пальто чи тренч", "не хочу привертати уваги"]
ПОЛЯ = ("нагода", "місце", "година", "темп_c", "опади", "реєстр_людини", "бажання", "вето", "настрій", "прикраси", "мета", "намір")
СЦ = dict(година=11, темп_c=18)
КОРОТКИЙ = ("Жінка сказала стилістці: «%s». Розклади ЛИШЕ сказане нею в JSON з полями: нагода, місце, дрес_код, бажання "
            "(список), вето {типи, кольори, принти, тканини, зони} (лише те, від чого вона відмовилась), настрій (список), "
            "мета (лестити | приховати | експресія), прикраси. Чого вона не сказала — не пиши зовсім. Відповідь — лише JSON.")
def сире(т):
    м = re.search(r"```(?:json)?\s*([\s\S]*?)```", т); т = м.group(1) if м else т
    try: return json.loads(т[т.find("{"):т.rfind("}") + 1])
    except Exception: return None
def стисло(об):
    в = {k: v for k, v in (об.get("вето") or {}).items() if v} if isinstance(об.get("вето"), dict) else об.get("вето")
    return {k: (в if k == "вето" else об.get(k)) for k in ПОЛЯ if (в if k == "вето" else об.get(k)) not in (None, "", [], {}, "невідомо")}
тека = sys.argv[1]; os.makedirs(тека, exist_ok=True)
for м in [x for x in os.environ.get("MODELS", "").split(",") if x]:
    for і, ф in enumerate(ФРАЗИ, 1):
        п = КОРОТКИЙ % ф if os.environ.get("PROMPT") == "короткий" else ПН.промпт_паспорта(dict(СЦ), ф); т0 = time.time()
        з = urllib.request.Request(os.environ["MODEL_URL"].rstrip("/") + "/chat/completions", json.dumps(dict(model=м,
            max_tokens=1500, stream=False, reasoning_effort="none", messages=[dict(role="user", content=п)])).encode(),
            {"Content-Type": "application/json"})
        т = json.load(urllib.request.urlopen(з, timeout=1800))["choices"][0]["message"].get("content") or ""
        с = time.time() - т0; об = сире(т)
        open(os.path.join(тека, "%s__%02d.txt" % (re.sub(r"[^\w.-]+", "_", м), і)), "w", encoding="utf-8").write(ф + "\n\n" + т)
        код = стисло(ПН.паспорт_з_json(json.dumps(об, ensure_ascii=False), dict(СЦ), ф)) if об else {}
        print("%s · %02d «%s» · %.1f с · JSON %s\n   модель: %s\n   код:    %s · відповідь_людині: %s" % (
            м, і, ф[:60], с, "так" if об else "НІ", json.dumps(стисло(об) if об else {}, ensure_ascii=False)[:420],
            json.dumps(код, ensure_ascii=False)[:420], str((об or {}).get("відповідь_людині") or "")[:160]))
