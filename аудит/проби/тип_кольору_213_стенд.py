"""Стенд 2.13: знімок з id речей та окремою лічбою «без входу» кольору.

Запуск з джерела/: python ../аудит/проби/тип_кольору_213_стенд.py вихід.json [до.json].
На базі зберігає id; на голові бере ті самі id з її каталогу, незалежно від нового добору.
"""
import collections
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))
import стенд_знімок as С
import composer as КМ
import bridge as Б
import pipeline
import колір_річ as КР

вихід = Path(sys.argv[1])
база = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else None
ід, без = {}, collections.Counter()
в_річ, суд, питання = КМ.у_річ, С.образ_і_суд, КР.без_входу_кольору


def по_ід(річ, слот, *а, **к):
    """У прямому виклику стенда записати id або взяти фіксований id бази."""
    кадр = sys._getframe(1)
    if кадр.f_code.co_filename.endswith("стенд_знімок.py"):
        назва = кадр.f_locals.get("назва") or кадр.f_back.f_locals.get("назва")
        if назва is not None:
            if база:
                номер = база["ід"][назва][слот]
                річ = next(р for р in Б.каталог_останнього_пакета() if р["id"] == номер)
            ід.setdefault(назва, {})[слот] = річ["id"]
    return в_річ(річ, слот, *а, **к)


def без_кольору(*а, **к):
    """Порахувати справжній емітований запис з нульовою силою, без зміни результату."""
    р = питання(*а, **к)
    без[(р["правило"], р["сила_нп_джерело"])] += 1
    return р


def з_охопленням(назва, сцена):
    """Дописати до суду його окреме охоплення кольором."""
    без.clear()
    р = суд(назва, сцена)
    р["без_входу_кольору"] = {"%s/%s" % к: в for к, в in sorted(без.items())}
    return р


for модуль in list(sys.modules.values()):
    if модуль is sys.modules[__name__]:
        continue
    for ім, значення in list(getattr(модуль, "__dict__", {}).items()):
        if значення is питання:
            setattr(модуль, ім, без_кольору)
КМ.у_річ, С.образ_і_суд = по_ід, з_охопленням
знімок = С.знімок()
вихід.write_text(json.dumps(dict(ід=ід, знімок=знімок), ensure_ascii=False, indent=2), encoding="utf-8")
print("Стенд збережено:", вихід, "сцен:", len(знімок), "фіксованих наборів:", len(ід))
