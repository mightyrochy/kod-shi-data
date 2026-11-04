"""ДО → ПІСЛЯ: <SHA бази> [JSON повного каталогу]; каталог підготовлено командою CI."""
import json, subprocess, sys, types
from collections import Counter
from pathlib import Path


def мірило(база, файл_каталогу=None):
    """Лічить переходи K-WEA-06 і звіряє тотожність усіх інших знахідок."""
    корінь = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(корінь / "джерела"))
    import feed as Ф
    import суд_погода as П
    до = types.ModuleType("погода_до")
    текст = subprocess.check_output(["git", "show", база + ":джерела/суд_погода.py"], cwd=корінь)
    exec(compile(текст, "погода_до.py", "exec"), до.__dict__)
    каталог = (json.loads(Path(файл_каталогу).read_text(encoding="utf-8")) if файл_каталогу else
               Ф._прочитати_каталог(Ф.каталог_на_диску("каталог_повний.xml"), ліміт_фото=0)["каталог"])
    взуття = [р for р in каталог if р.get("слот") == "взуття"]
    підсумки = []
    for темп in (-5, 2, 2.25):
        лічба = Counter()
        for річ in взуття:
            було = до.сезон_і_погода([річ], темп_c=темп)
            стало = П.сезон_і_погода([річ], темп_c=темп)
            assert [з for з in було if з["правило"] != "K-WEA-06"] == [з for з in стало if з["правило"] != "K-WEA-06"]
            старі = [з for з in було if з["правило"] == "K-WEA-06"]
            нові = [з for з in стало if з["правило"] == "K-WEA-06"]
            assert len(старі) == len(нові)
            for а, б in zip(старі, нові):
                лічба[а["сила"] + " → " + б["сила"]] += 1
                assert (а["сила"], б["сила"]) in (("default", "soft"), ("питання", "питання"))
        підсумки.append(dict(темп_c=темп, переходи=dict(лічба)))
    return dict(база=база, каталог=len(каталог), взуття=len(взуття), виміри=підсумки)


if __name__ == "__main__":
    print(json.dumps(мірило(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), ensure_ascii=False, indent=2))
