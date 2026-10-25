"""5.4-Г, рішення менеджера (1): скільки кодів відповіді V4 стали unknown лише тому, що рядок `evidence` не дав
їм пункту (пара «код — цитата» розірвана). Без моделі, над сирими відповідями теки V4 (404_г, проба 100):
python3 проби/лічба_без_доказу_v4_54г.py <тека V4> · Друкує: коди, що потребують цитати (не unknown; not_applicable — лише тип), з пунктом і без, за полями; набори
(set_parts) з їхніми цитатами. Пише <тека>/розбір_з_парою.json: той самий сторож цитат, а коду без пункту дано
цитату-назву речі (тримається завжди; мірці — ні, бо число в назві не стоїть) — верхня межа «скільки дала б
пара», її судить `проби/еталон_частки.py <тека>/розбір_з_парою.json` поруч із 404_г."""
import json, sys, collections; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір as КР, каталог_розбір_прогін as П
тека = Path(sys.argv[1])
лік, за_полем, набори, вих = collections.Counter(), collections.Counter(), [], {}
for р in json.load(open(тека / "прогін.json", encoding="utf-8"))["речі"]:
    дані, відп = П.розділити(open(тека / р["файл"], encoding="utf-8").read())
    try:
        об = json.loads(відп); докази, коди = ({к: в for к, _, в in (п.partition("=") for п in об[ключ].split(";") if п)}
                                                for ключ in ("evidence", "codes"))
    except (ValueError, KeyError, AttributeError):
        лік["не V4"] += 1; continue
    дерево = {}
    for ш, к, _ in КР.ПОЛЯ:
        кр = КР._кроки(ш); ім, список = кр[0]
        пункти = [x for x in коди.get(КР._ключ_коду(ш), "").split(",") if x] if список else [коди.get(КР._ключ_коду(ш), "unknown")]
        пари = []
        for і, код in enumerate(пункти):
            шд, мірка = (ш.replace("[]", "[%d]" % і) if список else ш), isinstance(к, КР.Мірка) and " " in код
            if код != "unknown" and кр[-1][0] != "slot" and (код != КР.НЕ_СТОСУЄТЬСЯ or ш == КР.ТИП):
                лік["з пунктом" if шд in докази else "без пункту" + (" (мірка)" if мірка else "")] += 1
                за_полем[ш] += шд not in докази
            ц = докази.get(шд) or дані.get("name", "")
            пари.append(dict(quote=ц, value=код.partition(" ")[0], unit=код.partition(" ")[2]) if мірка else dict(quote=ц, value=код))
        if len(кр) == 1: дерево[ім] = пари if список else пари[0]
        elif список: дерево[ім] = [dict(ч, **{кр[1][0]: п}) for ч, п in zip(дерево.get(ім, [{}] * len(пари)), пари)]
        else: дерево.setdefault(ім, {})[кр[1][0]] = пари[0]
    дерево["features"] = [dict(quote=ц, value=ф) for ц, _, ф in (п.partition("=") for п in об.get("features", "").split(";") if п)]
    вих[р["id"]] = КР.з_відповіді(json.dumps(дерево, ensure_ascii=False), дані)[0]
    if коди.get("set_parts.item_type"):
        набори.append((р["id"], коди.get("set_kind"), коди.get("set_parts.item_type"), {к: в for к, в in докази.items() if к.startswith("set_parts")}, дані.get("name", "")[:60]))
json.dump(вих, open(тека / "розбір_з_парою.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("речей %d; кодів, що потребують цитати: %s; без пункту за полями: %s" % (len(вих), dict(лік), [кн for кн in за_полем.most_common(12) if кн[1]]))
print("набори (id, set_kind, set_parts.item_type, їхні пункти evidence, назва):"); [print("  ", *н) for н in набори]
