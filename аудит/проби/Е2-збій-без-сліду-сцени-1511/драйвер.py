#!/usr/bin/env python3
"""Прилад проби (не код продукту): сцени зі збоєм наряду Е2-збій-без-сліду-сцени у хмарі через рв6_стенд.js і
сервер_claude.py — копія `Корені-нуль-живе-мірило-1511/драйвер.py` (той самий шлях і модель), сцени — п'ять нових рядків
реєстру з `ZBIJ=<вид>` (засіб наведення — `аудит/проби/збій_наведення.js`), SHA — `main` збірки.
Запуск: python3 драйвер.py <воркер> <кількість воркерів> <SHA збірки>. Фото сцени — TEKA_FOTO_SCENY."""
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ТЕКА = Path(__file__).resolve().parent; КОРІНЬ = ТЕКА.parents[2]
В, К, SHA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]; ПОРТ = 8790 + В
СЦЕНИ = [  # (id, режим) — сцени зі збоєм наряду Е2-збій-без-сліду-сцени (живі_сцени.txt, ZBIJ=<вид>)
    ("ж7_збій_битої_речі", "повне"), ("ж7_збій_помад", "повне"), ("ж7_збій_сховища", "повне"),
    ("ж7_збій_читання_фото", "повне"), ("ж7_збій_запису_кадру", "повне")]
журнал = ТЕКА / f"журнал_викликів_{В}.jsonl"
сервер = subprocess.Popen([sys.executable, str(ТЕКА / "сервер_claude.py"), str(ПОРТ), str(журнал)])
time.sleep(2)
for id_, режим in СЦЕНИ[В::К]:
    д = ТЕКА / id_
    if (д / "результат.json").exists(): continue
    д.mkdir(exist_ok=True); (д / "знімки").mkdir(exist_ok=True); (д / "VIDPOVIDI").mkdir(exist_ok=True)
    зм = json.loads(subprocess.check_output([sys.executable, str(КОРІНЬ / "аудит/проби/записати_сцену.py"), "--сцена", id_,
        "--режим", режим, "--лише-змінні"], text=True, cwd=КОРІНЬ))
    зм_ = {к: в for к, в in зм.items() if к not in ("MODEL", "MODEL_MOVA")}
    env = dict(os.environ, **зм_, MODEL="claude-sonnet-5-5", MODEL_MOVA="claude-sonnet-5-5", MODEL_URL=f"http://127.0.0.1:{ПОРТ}/v1",
               VIDPOVIDI=str(д / "VIDPOVIDI"), ZNIMKY=str(д / "знімки"), ZVIT_OUT=str(д / "вердикти.txt"),
               CHROMIUM="/opt/pw-browsers/chromium", NODE_PATH="/opt/node-tools/node_modules")
    (д / "код.txt").write_text(f"{SHA} {id_} ПІСЛЯ claude-sonnet-5-5+claude-sonnet-5-5\n", encoding="utf-8")
    ч0 = time.time(); п0 = datetime.now(timezone.utc).isoformat()
    cmd = ["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", "/tmp/стенд", "/tmp/pyodide", "3"]
    with open(д / "лог.txt", "w", encoding="utf-8") as л:
        rc = subprocess.run(cmd, cwd=КОРІНЬ, env=env, stdout=л, stderr=subprocess.STDOUT).returncode
    ч1 = time.time()
    рядки = [json.loads(р) for р in журнал.read_text(encoding="utf-8").splitlines()] if журнал.exists() else []
    поч = time.strftime("%H:%M:%S", time.gmtime(ч0)); кін = time.strftime("%H:%M:%S", time.gmtime(ч1))
    ціна_к = [з for з in рядки if поч <= з["початок_utc"] <= кін]
    ціна = {"викликів": len(ціна_к), "usd": round(sum(з["usd"] for з in ціна_к), 4), "вихід": sum(з.get("вихід") or 0 for з in ціна_к),
            "не200": sum(1 for з in ціна_к if з["статус"] != 200)}
    рез = {"початок": п0, "кінець": datetime.now(timezone.utc).isoformat(), "sha": SHA, "сцена": id_, "режим": режим,
           "rc": rc, "секунд": round(ч1 - ч0), "змінні": {к: зм[к] for к in зм if к not in ("CHAT_TEXT",)}, "claude_p": ціна}
    (д / "результат.json").write_text(json.dumps(рез, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(ТЕКА / "done.txt", "a", encoding="utf-8") as f:
        f.write(json.dumps({"сцена": id_, "rc": rc, "секунд": рез["секунд"], "час": рез["кінець"], **ціна}, ensure_ascii=False) + "\n")
сервер.terminate()
