# -*- coding: utf-8 -*-
"""Проба: РЯДОК ОСОБЛИВОСТЕЙ `features` у розборі каталогу — друкує факт, моделі не кличе. Збережені відповіді Н-1
(60 речей × MamayLM, Lapa; промпт v1 без поля) і заглушка з полем (ті самі відповіді + `features` кожної форми): вид
форми; коди — ті самі, що до правки (`каталог_розбір` на 66eb52c); довжина промпта до/після, uk і en, на тих 60 речах.
Запуск: python3 джерела/проби/каталог_розбір_особливості.py [тека з розпакованим p3/]"""
import collections, glob, json, os, subprocess, sys, tarfile, tempfile, types  # noqa: E401
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)  # noqa: E702
import каталог_розбір as КР, фід_каталог as ФК, фід_розбір as ФР               # noqa: E401,E402
ДО = types.ModuleType("каталог_розбір_до"); ДО.__file__ = КР.__file__             # noqa: E702
exec(subprocess.run(["git", "-C", Д, "show", "66eb52c:джерела/каталог_розбір.py"], capture_output=True, text=True, check=True).stdout, ДО.__dict__)
тека = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
if len(sys.argv) < 2: tarfile.open(os.path.join(Д, "..", "аудит", "тести", "сирі_2026-09-26", "p3_katalog_rozbir.tar.gz")).extractall(тека)  # noqa: E701
ФОРМИ = {"прийнято": "tok " * 9, "довгий фрагментами": ", ".join(["tok tok tok"] * КР.СТЕЛЯ_СЛІВ), "довгий суцільний": "tok " * 2 * КР.СТЕЛЯ_СЛІВ,
         "кирилиця": "tok ток", "unknown": "unknown", "нема поля": None, "не рядок": {"tok": 1}, "список": ["tok tok", "tok"]}
вид = lambda з, пр: "+".join(п.split(": ", 1)[1].split(" — ")[0] for п in пр if п.startswith("features:")) or (  # noqa: E731
    "unknown" if з == КР.UNKNOWN else "прийнято")
без = lambda п: {к: в for к, в in (п or {}).items() if к != КР.ОСОБЛИВОСТІ}                                        # noqa: E731
н1, коди, причини, ідс, заг = collections.Counter(), 0, 0, [], {ф: [collections.Counter(), 0, ""] for ф in ФОРМИ}
for ш in sorted(glob.glob(os.path.join(тека, "**", "прогін.json"), recursive=True)):
    for р in json.load(open(ш, encoding="utf-8"))["речі"]:
        сире = open(os.path.join(os.path.dirname(ш), р["файл"]), encoding="utf-8").read().split("── ВІДПОВІДЬ", 1)[-1]
        (до, пр_до), (після, пр) = ДО.з_відповіді(сире), КР.з_відповіді(сире)
        н1[вид((після or {}).get(КР.ОСОБЛИВОСТІ), пр)] += 1; ідс.append(р["id"])                    # noqa: E702
        коди += без(після) == (до or {}); причини += [п for п in пр if not п.startswith("features:")] == пр_до  # noqa: E702
        об = КР._ПР.розібрати_json(сире.replace(КР.ВСТАВКА, "")); об = об if isinstance(об, dict) else {}  # noqa: E702
        for ф, з in ФОРМИ.items():
            п2, пр2 = КР.з_відповіді(json.dumps(dict(об, **({} if з is None else {КР.ОСОБЛИВОСТІ: з})), ensure_ascii=False))
            заг[ф][0][вид(п2[КР.ОСОБЛИВОСТІ], пр2)] += 1; заг[ф][1] += без(п2) == (до or {})           # noqa: E702
            заг[ф][2] = "%r ← %s" % (п2[КР.ОСОБЛИВОСТІ], "; ".join(п for п in пр2 if п.startswith("features:")) or "без причини")
print("Н-1 (промпт v1 без поля), відповідей %d: features — %s · коди ті самі, що до правки: %d з %d · інші причини ті "
      "самі: %d з %d" % (len(ідс), dict(н1), коди, len(ідс), причини, len(ідс)))
print("заглушка з полем (ті самі %d відповідей, поле кожної форми):" % len(ідс))
for ф, (к, с, приклад) in заг.items():
    print("  %-19s → %s · коди ті самі %d з %d · %s" % (ф, dict(к), с, len(ідс), приклад[:150]))
офери = {o["id"]: o for o in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]}
речі = [офери[і] for і in dict.fromkeys(ідс)]
for м in ("uk", "en"):
    до, після = ([len(json.dumps(мод.промпт(o, м), ensure_ascii=False, indent=1)) for o in речі] for мод in (ДО, КР))
    print("промпт %s на %d речах: до %d знаків (середнє), після %d · +%d знаків, +%.1f %%, правил %d → %d" % (м, len(речі), sum(до) / len(до),
          sum(після) / len(після), (sum(після) - sum(до)) / len(до), 100.0 * (sum(після) - sum(до)) / sum(до), len(ДО.РОЗБІР[м].правила), len(КР.РОЗБІР[м].правила)))
