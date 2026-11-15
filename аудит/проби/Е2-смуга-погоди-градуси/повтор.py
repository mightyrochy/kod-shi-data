#!/usr/bin/env python3
"""Прилад проби (не код продукту): сцени живого мірила кореня Е2-смуга-погоди з прогону 15.11 (#3878) — записані
відповіді моделей (`replay_сцени.py`) на збірці дерева через `рв6_стенд.js`, той самий режим і змінні сцени.
Запуск: python3 повтор.py <тека записів 1511> <тека збірки> <тека pyodide> <тека виходу> <порт> [сцена…]."""
import json, os, subprocess, sys, time
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[3]
ЗАПИСИ, ЗБІРКА, PYODIDE, ВИХІД, ПОРТ = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]), int(sys.argv[5])
СЦЕНИ = {"ж8_зима": "повне", "ж1_екскурсія_бруківка": "повне", "ж7_мінус_вісім_пішки": "розмова",
         "ж2_різдвяна_вечеря": "розмова", "ж7_робота_можливо_дощ": "розмова", "ж2_новорічна_мороз": "повне OTSINKA=1"}
for id_ in sys.argv[6:] or СЦЕНИ:
    д = ВИХІД / id_
    for т in ("знімки", "VIDPOVIDI"):
        (д / т).mkdir(parents=True, exist_ok=True)
    зм = json.loads(subprocess.check_output([sys.executable, str(КОРІНЬ / "аудит/проби/записати_сцену.py"), "--сцена", id_,
                                             "--режим", СЦЕНИ[id_], "--лише-змінні"], text=True, cwd=КОРІНЬ))
    сервер = subprocess.Popen([sys.executable, str(КОРІНЬ / "аудит/проби/replay_сцени.py"), str(ЗАПИСИ / id_), str(ПОРТ)],
                              stdout=open(д / "повтор.log", "w", encoding="utf-8"), stderr=subprocess.STDOUT,
                              cwd=КОРІНЬ / "аудит/проби")
    time.sleep(3)
    env = dict(os.environ, **{к: в for к, в in зм.items() if к not in ("MODEL", "MODEL_MOVA")},
               MODEL="claude-sonnet-5-5", MODEL_MOVA="claude-sonnet-5-5", MODEL_URL=f"http://127.0.0.1:{ПОРТ}/v1",
               VIDPOVIDI=str(д / "VIDPOVIDI"), ZNIMKY=str(д / "знімки"), ZVIT_OUT=str(д / "вердикти.txt"),
               CHROMIUM="/opt/pw-browsers/chromium", NODE_PATH="/opt/node-tools/node_modules")
    ч0 = time.time()
    with open(д / "лог.txt", "w", encoding="utf-8") as л:
        rc = subprocess.run(["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:%d" % (ПОРТ + 100),
                             ЗБІРКА, PYODIDE, "3"], cwd=КОРІНЬ, env=env, stdout=л, stderr=subprocess.STDOUT).returncode
    сервер.terminate()
    print(json.dumps({"сцена": id_, "rc": rc, "секунд": round(time.time() - ч0)}, ensure_ascii=False), flush=True)
