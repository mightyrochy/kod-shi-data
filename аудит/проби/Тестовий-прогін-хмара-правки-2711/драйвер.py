#!/usr/bin/env python3
"""Прилад проби (не код продукту): сцени наряду Тестовий-прогін-хмара-правки-2711 у хмарі через рв6_стенд.js, ZHYVA=sonnet
(`claude -p` самого стенда). Копія `Тестовий-прогін-хмара-1811-ранок/драйвер.py`: змінено перелік сцен і додано проходи.
Перший прохід сцени — у теці `<сцена>/` (її лічить прилад `живий_після_прогнано.py`), решта — `<сцена>__прохід<N>/`.
Запуск: python3 драйвер.py <воркер> <кількість воркерів> <SHA збірки>."""
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ТЕКА = Path(__file__).resolve().parent; КОРІНЬ = ТЕКА.parents[2]
В, К, SHA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
СЦЕНИ = [  # (id, режим, проходів)
    ("ж3_свято_др_взуття_фото", "повне +фото", 2),
    ("ж1_театр_максі_підбір", "повне", 2),
    ("ж1_17102_краї_утримано", "повне DO=otsinka OTSINKA=1", 8),
    ("ж1_17102_краї_перевірено", "повне DO=otsinka OTSINKA=1", 2),
    ("17009", "палітра", 2)]
РОБОТИ = [(і, р, п) for і, р, к in СЦЕНИ for п in range(1, к + 1)]
for id_, режим, п in РОБОТИ[В::К]:
    д = ТЕКА / (id_ if п == 1 else f"{id_}__прохід{п}")
    if (д / "результат.json").exists(): continue
    д.mkdir(exist_ok=True); (д / "знімки").mkdir(exist_ok=True); (д / "VIDPOVIDI").mkdir(exist_ok=True)
    арг = [sys.executable, str(КОРІНЬ / "аудит/проби/записати_сцену.py"), "--сцена", id_, "--лише-змінні"]
    if id_ != "17009": арг += ["--режим", режим]
    зм = json.loads(subprocess.check_output(арг, text=True, cwd=КОРІНЬ))
    зм_ = {к: в for к, в in зм.items() if к not in ("MODEL", "MODEL_MOVA")}
    env = dict(os.environ, **зм_, ZHYVA="sonnet",
               VIDPOVIDI=str(д / "VIDPOVIDI"), ZNIMKY=str(д / "знімки"), ZVIT_OUT=str(д / "вердикти.txt"),
               CHROMIUM="/opt/pw-browsers/chromium", NODE_PATH="/opt/node-tools/node_modules")
    (д / "код.txt").write_text(f"{SHA} {id_} ПІСЛЯ claude-sonnet (ZHYVA)+claude-sonnet (ZHYVA)\n", encoding="utf-8")
    ч0 = time.time(); п0 = datetime.now(timezone.utc).isoformat()
    cmd = ["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", "/tmp/стенд", "/tmp/pyodide", "3"]
    with open(д / "лог.txt", "w", encoding="utf-8") as л:
        rc = subprocess.run(cmd, cwd=КОРІНЬ, env=env, stdout=л, stderr=subprocess.STDOUT).returncode
    ч1 = time.time()
    рез = {"початок": п0, "кінець": datetime.now(timezone.utc).isoformat(), "sha": SHA, "сцена": id_, "прохід": п, "режим": режим,
           "rc": rc, "секунд": round(ч1 - ч0), "змінні": {к: зм[к] for к in зм if к not in ("CHAT_TEXT",)}}
    (д / "результат.json").write_text(json.dumps(рез, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(ТЕКА / "done.txt", "a", encoding="utf-8") as f:
        f.write(json.dumps({"сцена": id_, "прохід": п, "rc": rc, "секунд": рез["секунд"], "час": рез["кінець"]}, ensure_ascii=False) + "\n")
