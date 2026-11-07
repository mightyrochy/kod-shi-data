"""Чи доходить її hex до рядка місця: повтор записаних обмінів мосту (входи — оцінка моделі) з її hex як є і зі
зсунутим; на кожному рядку з переліку — відбиток простих значень імен, що стоять у самому рядку, при кожному
виконанні (до 3000).
Відбитки різні — її hex доходить до рядка; однакові — рядок виконується, але не з її значення; 0 — не виконується.
Запуск: python3 збурення.py <корінь> <вивід> <вивід приладу> <0|1 — зсунути її hex> [сцени через кому — типово
палітра_її,плитка_робота; «усі» — усі записи `аудит/проби/знімок_входи`]"""
import asyncio, hashlib, json, os, re, sys, tempfile, threading
from pathlib import Path
К = Path(sys.argv[1]).resolve(); вивід = Path(sys.argv[2]); зсув = sys.argv[4] == "1"
місця = {}
for р in open(sys.argv[3], encoding="utf8", errors="replace"):
    м = re.match(r"\s*(джерела/[^ :]+):(\d+)", р)
    if м and (" · п." in р or " — " in р):
        місця.setdefault(str(К / м.group(1)), set()).add(int(м.group(2)))
відбитки = {}
імена_рядка = {}


def _імена(ф, л):
    """Імена, що стоять у рядку місця (локальні значення, які рядок читає)."""
    if (ф, л) not in імена_рядка:
        try:
            р = Path(ф).read_text("utf8").splitlines()[л - 1]
        except (OSError, IndexError):
            р = ""
        р = re.sub(r"#.*$", "", re.sub(r"(\"[^\"]*\"|'[^']*')", "", р))
        імена_рядка[(ф, л)] = set(re.findall(r"[^\W\d]\w*", р))
    return імена_рядка[(ф, л)]


def _просте(в):
    if isinstance(в, float):
        return repr(round(в, 6))
    if isinstance(в, (int, str, bool, type(None))):
        return repr(в)[:200]
    if isinstance(в, (tuple, list)) and len(в) <= 12 and all(isinstance(x, (int, float, str, type(None))) for x in в):
        return repr([round(x, 6) if isinstance(x, float) else x for x in в])[:300]
    if isinstance(в, dict) and len(в) <= 30:
        return repr(sorted((str(к), _просте(з)) for к, з in в.items() if _просте(з) is not None))[:600]
    return None


def _лок(frame, ev, arg):
    if ev == "line":
        ф = frame.f_code.co_filename
        if frame.f_lineno in місця.get(ф, ()):
            сп = відбитки.setdefault((ф, frame.f_lineno), [])
            if len(сп) < 3000:
                імена = _імена(ф, frame.f_lineno)
                лок = sorted((к, _просте(в)) for к, в in frame.f_locals.items() if к in імена)
                сп.append(hashlib.md5(repr([x for x in лок if x[1] is not None]).encode()).hexdigest()[:10])
    return _лок


def _гл(frame, ev, arg):
    return _лок if frame.f_code.co_filename in місця else None


def _зсунути(о):
    """Її hex (шкіра, волосся, очі, кільце) — на кілька одиниць RGB: інша оцінка моделі того самого портрета."""
    if isinstance(о, dict):
        return {к: (_hex(в) if к in ("шкіра", "волосся", "очі", "очі_кільце") else _зсунути(в)) for к, в in о.items()}
    if isinstance(о, list):
        return [_зсунути(в) for в in о]
    return о


def _hex(в):
    if isinstance(в, list):
        return [_hex(x) for x in в]
    if isinstance(в, str) and re.fullmatch(r"#?[0-9a-fA-F]{6}", в):
        h = в.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = min(255, r + 9), max(0, g - 4), max(0, b - 11)
        return "#%02x%02x%02x" % (r, g, b)
    return _зсунути(в)


sys.path.insert(0, str(К / "джерела/прилади"))
import знімок_мосту as З
З.підготувати(str(К / "джерела"))
import feed
feed.каталог_на_диску("каталог_brief.xml")
кеш = Path(tempfile.mkdtemp()) / "кольори-збурення.json"
кеш.write_text("{}", "utf8")
threading.settrace(_гл)
sys.settrace(_гл)
СЦЕНИ = sys.argv[5] if len(sys.argv) > 5 else "палітра_її,плитка_робота"
if СЦЕНИ == "усі":
    СЦЕНИ = ",".join(sorted(п.name[:-len(".jsonl.gz")] for п in (К / "аудит/проби/знімок_входи").glob("*.jsonl.gz")))
for сцена in СЦЕНИ.split(","):
    запис = З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz")))
    рядки = [json.loads(р) for р in запис.splitlines() if р.strip()]
    for рядок in рядки:
        вхід = json.loads(рядок["вхід"])
        if зсув:
            вхід = _зсунути(вхід)
        if isinstance(вхід, dict) and "кеш_кольорів" in вхід:
            вхід["кеш_кольорів"] = str(кеш)
        рядок["вхід"] = json.dumps(вхід, ensure_ascii=False)
    знімок, час = asyncio.run(З.прогнати("\n".join(json.dumps(р, ensure_ascii=False) for р in рядки)))
    записи = [json.loads(р) for р in знімок.splitlines()][1:]
    print(сцена, len(записи), "винятків", sum("помилка" in з for з in записи), flush=True)
sys.settrace(None)
вих = {"%s:%d" % (os.path.relpath(ф, К), л): відбитки.get((ф, л), []) for ф, лл in місця.items() for л in лл}
вивід.write_text(json.dumps(вих, ensure_ascii=False, sort_keys=True), "utf8")
print("рядків", len(вих), "виконується", sum(1 for в in вих.values() if в))
