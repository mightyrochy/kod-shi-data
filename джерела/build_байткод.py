"""Байткод повного показу для Python 3.12 у Pyodide 0.26.4.

Компілятор окремий від Python збирача; читає рівно запаковані .py, а не локальний __pycache__.
"""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys

МАНІФЕСТ = "байткод.json"
MAGIC = "cb0d0d0a"
ТЕГ = "cpython-312"

_КОМПІЛЯТОР = r'''
import base64, importlib.util, json, marshal, sys
if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
    sys.exit("байткод: потрібен CPython 3.12")
if importlib.util.MAGIC_NUMBER.hex() != "cb0d0d0a" or sys.implementation.cache_tag != "cpython-312":
    sys.exit("байткод: несумісний magic або cache_tag")
модулі = json.load(sys.stdin)
вихід = {}
for імя, рядок in sorted(модулі.items()):
    код = base64.b64decode(рядок)
    тіло = compile(код, "/показ/" + імя, "exec", dont_inherit=True, optimize=0)
    pyc = (importlib.util.MAGIC_NUMBER + (3).to_bytes(4, "little")
           + importlib.util.source_hash(код) + marshal.dumps(тіло))
    вихід["__pycache__/" + імя[:-3] + ".cpython-312.pyc"] = base64.b64encode(pyc).decode("ascii")
json.dump({"версія": sys.version, "файли": вихід}, sys.stdout, ensure_ascii=False)
'''

ПЕРЕВІРКА = r'''
import hashlib, importlib.util, json, os, sys, warnings
with open("/показ/байткод.json", encoding="utf-8") as ф:
    _бм = json.load(ф)
_бсум = hashlib.sha256()
_бпридатних = 0
_бвідкинуто = []
_бсумісний = (sys.implementation.cache_tag == _бм["cache_tag"]
                and importlib.util.MAGIC_NUMBER.hex() == _бм["magic"])
for _бі, _бмета in sorted(_бм["модулі"].items()):
    _бдж = open("/показ/" + _бі, "rb").read()
    _бсум.update(_бі.encode("utf-8") + b"\0" + _бдж)
    if hashlib.sha256(_бдж).hexdigest() != _бмета["source_sha256"]:
        raise RuntimeError("байткод: джерело розійшлося з маніфестом: " + _бі)
    _бшлях = "/показ/" + _бмета["pyc"]
    try:
        _бкод = open(_бшлях, "rb").read()
    except FileNotFoundError:
        _бкод = b""
    _бвалідний = (_бсумісний and len(_бкод) >= 16
        and _бкод[:4] == importlib.util.MAGIC_NUMBER
        and int.from_bytes(_бкод[4:8], "little") == 3
        and _бкод[8:16] == importlib.util.source_hash(_бдж)
        and hashlib.sha256(_бкод).hexdigest() == _бмета["pyc_sha256"])
    if _бвалідний:
        _бпридатних += 1
    else:
        if os.path.exists(_бшлях):
            os.unlink(_бшлях)
        _бвідкинуто.append(_бі)
if _бсум.hexdigest() != _бм["source_sha256"]:
    raise RuntimeError("байткод: SHA джерел не збігається")
БАЙТКОД_СТАН = {"придатних": _бпридатних, "відкинуто": _бвідкинуто,
                  "source_sha256": _бм["source_sha256"], "cache_tag": sys.implementation.cache_tag,
                  "magic": importlib.util.MAGIC_NUMBER.hex()}
if _бвідкинуто:
    warnings.warn("байткод: запасний шлях .py для %d модулів; імпорт і час потребують виміру" % len(_бвідкинуто))
'''


def скомпілювати(модулі, компілятор=None):
    """Повертає свіжі checked-hash .pyc та маніфест SHA для цих самих байтів .py."""
    компілятор = компілятор or os.environ.get("LYUSTERKO_PYC_PYTHON")
    if not компілятор:
        компілятор = sys.executable if sys.version_info[:2] == (3, 12) else shutil.which("python3.12")
    if not компілятор:
        raise RuntimeError("байткод: CPython 3.12 недоступний; задайте LYUSTERKO_PYC_PYTHON")
    вхід = {і: base64.b64encode(д).decode("ascii") for і, д in sorted(модулі.items())}
    процес = subprocess.run([компілятор, "-I", "-c", _КОМПІЛЯТОР],
        input=json.dumps(вхід), capture_output=True, text=True, check=False)
    if процес.returncode:
        raise RuntimeError("байткод: компілятор відмовив: " + процес.stderr.strip())
    відповідь = json.loads(процес.stdout)
    файли = {і: base64.b64decode(д) for і, д in відповідь["файли"].items()}
    сум = hashlib.sha256()
    маніфест = {"pyodide": "0.26.4", "magic": MAGIC, "cache_tag": ТЕГ,
                "компілятор": відповідь["версія"], "модулі": {}}
    for імя, код in sorted(модулі.items()):
        шлях = "__pycache__/" + імя[:-3] + "." + ТЕГ + ".pyc"
        сум.update(імя.encode("utf-8") + b"\0" + код)
        маніфест["модулі"][імя] = {"source_sha256": hashlib.sha256(код).hexdigest(),
            "pyc": шлях, "pyc_sha256": hashlib.sha256(файли[шлях]).hexdigest()}
    маніфест["source_sha256"] = сум.hexdigest()
    файли[МАНІФЕСТ] = json.dumps(маніфест, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return файли
