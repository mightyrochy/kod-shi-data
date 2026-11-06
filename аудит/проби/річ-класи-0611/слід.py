"""Які місця приладу виконуються на записаних обмінах мосту (входи — оцінка моделі); знімки виходу — поруч з виводом."""
import asyncio, json, os, sys, tempfile, threading
from pathlib import Path
К = Path(sys.argv[1]).resolve(); вивід = Path(sys.argv[2])
місця = {}
for р in open(sys.argv[3], encoding="utf8", errors="replace"):
    if р.startswith("джерела/") and " · п." in р:
        ф, л = р.split(" · ")[0].rsplit(":", 1)
        місця.setdefault(str(К / ф), set()).add(int(л))
влучання = {}
def _лок(frame, ev, arg):
    if ev == "line":
        ф = frame.f_code.co_filename
        if frame.f_lineno in місця.get(ф, ()):
            влучання[(ф, frame.f_lineno)] = влучання.get((ф, frame.f_lineno), 0) + 1
    return _лок
def _гл(frame, ev, arg):
    return _лок if frame.f_code.co_filename in місця else None
sys.path.insert(0, str(К / "джерела/прилади"))
import знімок_мосту as З
З.підготувати(str(К / "джерела"))
import feed
feed.каталог_на_диску("каталог_brief.xml")
кеш = Path(tempfile.gettempdir()) / "кольори-слід.json"; кеш.write_text("{}", "utf8")
threading.settrace(_гл); sys.settrace(_гл)
for сцена in ("палітра_її", "плитка_робота"):
    запис = З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz")))
    рядки = [json.loads(р) for р in запис.splitlines() if р.strip()]
    for рядок in рядки:
        вхід = json.loads(рядок["вхід"])
        if "кеш_кольорів" in вхід: вхід["кеш_кольорів"] = str(кеш)
        рядок["вхід"] = json.dumps(вхід, ensure_ascii=False)
    знімок, час = asyncio.run(З.прогнати("\n".join(json.dumps(р, ensure_ascii=False) for р in рядки)))
    записи = [json.loads(р) for р in знімок.splitlines()][1:]
    (вивід.parent / (вивід.stem + "-" + сцена + ".jsonl")).write_text(знімок, "utf8")
    print(сцена, len(записи), "винятків", sum("помилка" in з for з in записи), flush=True)
sys.settrace(None)
рядки = []
for ф, лл in sorted(місця.items()):
    for л in sorted(лл):
        рядки.append("%s:%d\t%d" % (os.path.relpath(ф, К), л, влучання.get((ф, л), 0)))
вивід.write_text("\n".join(рядки) + "\n", "utf8")
print("виконується", sum(1 for р in рядки if not р.endswith("\t0")), "з", len(рядки))
