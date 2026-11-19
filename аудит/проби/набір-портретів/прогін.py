#!/usr/bin/env python3
"""Тестовий прогін із портретом (наряд Річ-ознаки-обличчя-набір-портретів, крок 3): сцена + `PORTRET=<файл набору>`, модель —
`ZHYVA=sonnet` (`claude -p` самого стенда). Копія `Тестовий-прогін-хмара-1811/драйвер.py` без журналу викликів.
Запуск: ZHYVA=sonnet python3 прогін.py <тека виходу> <тека портретів (збір.py)> <сцена>:<режим>:<кадр> … (кадр «-» — без портрета)
Збірка — /tmp/стенд/index.html, Pyodide — /tmp/pyodide (як у `аудит/проби/рв6_стенд.js`)."""
import json, os, subprocess, sys, time
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[3]
вих, портрети = Path(sys.argv[1]), Path(sys.argv[2])
for арг in sys.argv[3:]:
    id_, режим, кадр = арг.split(":")
    д = вих / id_; (д / "знімки").mkdir(parents=True, exist_ok=True); (д / "VIDPOVIDI").mkdir(exist_ok=True)
    зм = json.loads(subprocess.check_output([sys.executable, str(КОРІНЬ / "аудит/проби/записати_сцену.py"), "--сцена", id_,
        "--режим", режим, "--лише-змінні"], text=True, cwd=КОРІНЬ))
    зм = {к: в for к, в in зм.items() if к not in ("MODEL", "MODEL_MOVA")}
    env = dict(os.environ, **зм, **({"PORTRET": str(портрети / (кадр + ".jpg"))} if кадр != "-" else {}), VIDPOVIDI=str(д / "VIDPOVIDI"), ZNIMKY=str(д / "знімки"),
               ZVIT_OUT=str(д / "вердикти.txt"), CHROMIUM="/opt/pw-browsers/chromium", NODE_PATH="/opt/node-tools/node_modules")
    ч0 = time.time()
    with open(д / "лог.txt", "w", encoding="utf-8") as л:
        rc = subprocess.run(["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", "/tmp/стенд", "/tmp/pyodide", "3"],
                            cwd=КОРІНЬ, env=env, stdout=л, stderr=subprocess.STDOUT).returncode
    (д / "результат.json").write_text(json.dumps(dict(сцена=id_, режим=режим, кадр=кадр, rc=rc, секунд=round(time.time() - ч0), змінні={к: в for к, в in зм.items() if к != "CHAT_TEXT"}),
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print(id_, "rc", rc, round(time.time() - ч0), "с", flush=True)
