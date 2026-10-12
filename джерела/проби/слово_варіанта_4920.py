"""4920: слово переліку проти виміру фото; ДО — голова PR, ПІСЛЯ — робочий код."""
import gzip, json, os, subprocess, sys, tempfile, types
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import фід_варіант as ФВ, фід_збагачення as ФЗ, verify as V
from фід_розбір import читати_yml, _СЕП_КОЛЬОРУ
from фід_фото import _спільні_фото, чужий_кадр
ДО = types.ModuleType("варіант_до")
exec(subprocess.run(["git", "show", "54ec4bad4c351dea597b4c0dee0b1a7073bcc254:джерела/фід_варіант.py"],
                    capture_output=True, text=True, check=True).stdout, ДО.__dict__)
with gzip.open("../каталог_повний.xml.gz", "rb") as ф, tempfile.NamedTemporaryFile() as т:
    т.write(ф.read()); т.flush(); речі, _ = читати_yml(т.name)
збагачення, сестри = ФЗ.читати_збагачення(), ФВ.сестри_варіантів(речі)
спільні = _спільні_фото(речі)
лічба, зміни, залишок, без = [0, 0], [], [], 0
for р in речі:
    поле = р.get("колір_сирий") or р.get("колір_назва") or ""
    if len([ч for ч in поле.split(",") if ч.strip()]) < 2: continue
    з = збагачення.get(р["id"])
    if not ФЗ._збагачення_придатне(з) or чужий_кадр(з.get("фото"), спільні.get(р.get("магазин")) or {}):
        без += 1; continue
    фото, lab, дж = ФЗ.колір_збагачення(з)
    слова = [(ф(р, з, сестри) or {}).get("слово") or поле for ф in (ДО.слово_варіанта, ФВ.слово_варіанта)]
    слова = [next(ч.strip() for ч in _СЕП_КОЛЬОРУ.split(слово) if ч.strip()) for слово in слова]
    for і, слово in enumerate(слова):
        с = V.слово_крамниці(next(ч.strip() for ч in _СЕП_КОЛЬОРУ.split(слово) if ч.strip()))
        суд = V.перевірити(lab, ім=с["ім"]) if с else {"вердикт": "невідомо", "причини": ["слово поза лексиконом"]}
        погано = суд["вердикт"] != "прийнято"
        лічба[і] += погано
        if і == 1 and погано: залишок.append(dict(id=р["id"], слово=слово, причина=суд["причини"], джерело=дж))
    if слова[0] != слова[1]:
        зміни.append(dict(id=р["id"], до=слова[0], після=слова[1], фото=з.get("фото"), вимір=фото, джерело=дж))
print("ФАКТ · ДО %d, ПІСЛЯ %d; змінених слів %d; без придатного збагачення %d" % (*лічба, len(зміни), без))
for р in залишок: print("ЗАЛИШОК · " + json.dumps(р, ensure_ascii=False))
for р in зміни: print("ЗМІНА · " + json.dumps(р, ensure_ascii=False))
