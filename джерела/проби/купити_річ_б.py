"""Мірило Б наряду Функція-купити-річ: п'ять описів «знайди мені таку» викликом `find_item` (як його дає мовна модель
розмови) → `conversation_tools.прийняти_виклик` → `bridge.виклик("пошук_речі")` на каталозі з диска, тіло А, без
портрета; лічба (8)–(10), час. Кеш кольорів — тимчасовий файл, як `кеш.json` показу (офлайн його не переписують)."""
import sys, os, re, json, time, tempfile; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge, conversation_tools as CT, фід_каталог as ФК, оцінка_образу as ОО
ОПИСИ = [{"item_type": "skirt", "shine": "sequins_rhinestones"}, {"item_type": "skirt", "colour": "black", "length": "midi"},
         {"item_type": "skirt", "texture": "satin", "colour": "green"}, {"item_type": "trousers", "cut": "wide", "colour": "beige"},
         {"item_type": "shorts", "shine": "sequins_rhinestones", "colour": "yellow"}]   # останнього в каталозі нема
d = dict(зріст=160, обхвати={"плечі": 92, "груди": 88, "талія": 70, "стегна": 106, "високе_стегно": 92}, шкіра=[],
         волосся=[], очі=None, сценарій={}, колір_відмова="portrait_face_small", ліміт_фото=0, каталог=ФК.каталог_на_диску(),
         кеш_кольорів=os.path.join(tempfile.mkdtemp(), "кеш.json"))
# слова й сирі поля запису, якими крамниця чи фото кажуть ознаку (код опису → поля → корені слів)
СЛОВА = {"skirt": "спідниц", "trousers": "штан|брюк|палацо|палаццо|кюлот", "shorts": "шорт", "black": "чорн",
         "green": "зелен|смарагд|олив|хакі|м.ят|фісташ|салат", "beige": "беж|пісоч|кемел|тауп|карамел|молочн",
         "yellow": "жовт|гірчич|лимон", "midi": "міді|midi|литка", "satin": "сатин|атлас|satin",
         "wide": "широк|палацо|палаццо|кюлот|wide|flare|кльош", "sequins_rhinestones": "паєт|пайет|страз|sequin"}
ПОЛЯ = {"item_type": ("тип", "назва"), "colour": ("колір_назва", "колір_назва_крамниці", "назва"),
        "length": ("довжина_рівень", "довжина_рівень_крамниці", "назва"), "cut": ("крій", "крій_крамниці", "назва"),
        "texture": ("текстура", "матеріал", "назва"), "shine": ("текстура", "деталі_крою", "матеріал", "назва")}
def відповідає(з, поле, код):
    return bool(re.search(СЛОВА[код], " ".join(str(з.get(п) or "") for п in ПОЛЯ[поле]).lower()))
лічба, всі, з_оцінкою, нема, рядки, хиби = 0, 0, 0, 0, [], []
for н, опис in enumerate(ОПИСИ):
    прийнятий, вади = CT.прийняти_виклик({"name": "find_item", "args": опис})
    т = time.time()
    try: р = json.loads(bridge.виклик("пошук_речі", json.dumps(dict(d, опис=(прийнятий or {}).get("args") or {}))))
    except Exception as е: р = dict(варіанти=[], заяви=[], збій=repr(е)[:70])
    с, вв = time.time() - т, р.get("варіанти") or []
    коди = [з.get("code") for з in р.get("заяви") or []]
    try: кат = {str(з.get("id")): з for з in ОО._КЕШ_БЕЗ_ПУЛУ["б"][1]}
    except KeyError: кат = {}
    # звірка КОЖНОГО коду опису за записом каталогу варіанта — своїм словником проби, не читачами пошуку
    # (`пошук_речі.ЧИТАЧІ` добирали варіанти, тож звірка ними була колом — перевірка-1211-11 на #3578, дошка 14784)
    збіг = [all(відповідає(кат.get(в["ід"], {}), п, к) for п, к in опис.items()) for в in вв]
    хиби += ["%s %s: %s" % (в["ід"], в["назва"][:30], ",".join(п for п, к in опис.items()
                                                              if not відповідає(кат.get(в["ід"], {}), п, к))) for в, з in zip(вв, збіг) if not з][:2]
    if н < 4:
        лічба += bool(вв) and all(збіг)
    else:
        нема += not вв and "catalogue_has_none" in коди
    for в in вв:
        кв = [з["code"] for з in ((в.get("вердикт") or {}).get("повідомлення") or {}).get("statements") or []]
        всі += 1
        з_оцінкою += (any(к in кв for к in ("hem_on_her_body", "hem_not_judged")) and any(к in кв for к in ("rise_of_item", "rise_not_named"))
                      and any(к.startswith("colour_role_") for к in кв) and any(к.startswith("pairs_with_") for к in кв))
    рядки.append("  %s → %d вар. (%s) за %.1f с; без коду: %s; %s" % (опис, len(вв), "; ".join(в["назва"][:28] for в in вв[:2]),
                 с, р.get("без_коду"), р.get("збій") or ",".join(к for к in коди if к != "catalogue_records_without_code")))
print("Б: (8) %d/4 (9) %d/%d (10) %d/1" % (лічба, з_оцінкою, всі, нема)); print("\n".join(рядки))
if хиби: print("  не за словами запису:", "; ".join(хиби))
