"""Незалежна перевірка #3962: послідовні команди, повні стиснуті виводи й коди завершення."""
import gzip
import json
import os
import pathlib
import subprocess
import sys
import time

дерево = pathlib.Path(sys.argv[1]).resolve()
вихід = pathlib.Path(sys.argv[2]).resolve()
вихід.mkdir(parents=True, exist_ok=True)
джерела = дерево / "джерела"
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
команди = [
    ("стенд", [sys.executable, "-X", "utf8", "стенд_знімок.py", "--дим"], джерела),
    ("живий-шлях", [sys.executable, "-X", "utf8", "тест_живого_шляху.py"], джерела),
    ("протокол", [sys.executable, "-X", "utf8", "тест_протоколу.py"], джерела),
    ("розділи", [sys.executable, "-X", "utf8", "прилади/розділи_гейтів.py"], джерела),
    ("контракти", [sys.executable, "-X", "utf8", "audit_contracts.py"], джерела),
    ("показ", ["node", "тест_показу.js"], джерела),
    ("прилад", [sys.executable, "-X", "utf8", "джерела/прилади/корінь_е3_поле_без_писача.py"], дерево),
]
проби = sorted({*джерела.glob("проби/фокус_*.py"), *джерела.glob("проби/колір_відлуння_*.py")})
команди += [(п.stem, [sys.executable, "-X", "utf8", str(п.relative_to(джерела))], джерела) for п in проби]
команди.append(("заміна-з3", [sys.executable, "-X", "utf8", "проби/заміна_з3_колір.py",
                            "1e5ec4a428a2739431da49732df53e7f4e60419e"], джерела))
підсумок = []
for назва, команда, де in команди:
    print("ПОЧАТО", назва, flush=True)
    початок = time.monotonic()
    процес = subprocess.run(команда, cwd=де, env=оточення, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with gzip.open(вихід / (назва + ".txt.gz"), "wb") as файл:
        файл.write(процес.stdout)
    підсумок.append(dict(назва=назва, команда=команда, тека=str(де), код=процес.returncode,
                        секунд=round(time.monotonic() - початок, 2)))
    (вихід / "команди.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ЗАВЕРШЕНО", назва, "код", процес.returncode, "секунд", підсумок[-1]["секунд"], flush=True)
print("УСЬОГО", len(підсумок), "НЕ НУЛЬ", sum(п["код"] != 0 for п in підсумок), flush=True)
