#!/usr/bin/env python3
"""Спільний драйвер: тека прогону, JSON трійок [сцена, режим, прохід], воркер, кількість, SHA."""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]

def лічба_жива(тека):
    відповіді = тека / "VIDPOVIDI"
    if not відповіді.is_dir():
        raise FileNotFoundError(f"Нема запису викликів: {відповіді}")
    файли = (ф for ф in відповіді.iterdir() if ф.is_file() and re.fullmatch(r"seed\d+_\d+_.+\.txt", ф.name))
    кількість = sum(1 for ф in файли if "── ВІДПОВІДЬ (" in ф.read_text(encoding="utf-8"))
    return {"викликів": кількість, "usd": None, "вихід": None, "не200": None,
            "причина": "не лічено: ціна USD, вихідні токени та підсумок статусів сервера"}

def лічба_сервера(журнал, ч0, ч1):
    рядки = [json.loads(р) for р in журнал.read_text(encoding="utf-8").splitlines()] if журнал.exists() else []
    поч = time.strftime("%H:%M:%S", time.gmtime(ч0)); кін = time.strftime("%H:%M:%S", time.gmtime(ч1))
    ціна_к = [з for з in рядки if поч <= з["початок_utc"] <= кін]
    return {"викликів": len(ціна_к), "usd": round(sum(з["usd"] for з in ціна_к), 4),
            "вихід": sum(з.get("вихід") or 0 for з in ціна_к), "не200": sum(1 for з in ціна_к if з["статус"] != 200)}

def main():
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument("--лічити", type=Path, nargs="+", help="порахувати записані відповіді")
    парсер.add_argument("--сервер", type=Path, help="шлях до сервер_claude.py")
    парсер.add_argument("тека", type=Path, nargs="?")
    парсер.add_argument("сцени", type=Path, nargs="?", help="JSON: масив трійок [сцена, режим, прохід]")
    парсер.add_argument("воркер", type=int, nargs="?")
    парсер.add_argument("воркерів", type=int, nargs="?")
    парсер.add_argument("sha", nargs="?")
    а = парсер.parse_args()
    if а.лічити is not None:
        for тека in а.лічити:
            print(json.dumps({"тека": str(тека), **лічба_жива(тека)}, ensure_ascii=False))
        return
    if any(х is None for х in (а.тека, а.сцени, а.воркер, а.воркерів, а.sha)):
        парсер.error("потрібні тека, сцени, воркер, кількість воркерів і SHA")
    if not os.environ.get("ZHYVA") and not а.сервер:
        парсер.error("без ZHYVA потрібен шлях --сервер")
    if а.воркерів < 1 or not 0 <= а.воркер < а.воркерів:
        парсер.error("воркер має бути від 0 до кількості воркерів мінус один")
    СЦЕНИ = json.loads(а.сцени.read_text(encoding="utf-8"))
    if not isinstance(СЦЕНИ, list) or not all(isinstance(с, list) and len(с) == 3 and all(isinstance(х, str) and х for х in с) for с in СЦЕНИ):
        парсер.error("сцени мають бути списком трійок непорожніх рядків")
    ТЕКА = а.тека.resolve(); ТЕКА.mkdir(parents=True, exist_ok=True)
    В, К, SHA = а.воркер, а.воркерів, а.sha
    ПОРТ = 8790 + В
    ZHYVA = os.environ.get("ZHYVA")
    журнал = ТЕКА / f"журнал_викликів_{В}.jsonl"
    сервер = None if ZHYVA else subprocess.Popen([sys.executable, str(а.сервер.resolve()), str(ПОРТ), str(журнал)])
    time.sleep(2)
    for id_, режим, прох in СЦЕНИ[В::К]:
        д = ТЕКА / f"{id_}__{прох}"
        if (д / "результат.json").exists(): continue
        д.mkdir(exist_ok=True); (д / "знімки").mkdir(exist_ok=True); (д / "VIDPOVIDI").mkdir(exist_ok=True)
        зм = json.loads(subprocess.check_output([sys.executable, str(КОРІНЬ / "аудит/проби/записати_сцену.py"), "--сцена", id_,
            "--режим", режим, "--лише-змінні"], text=True, cwd=КОРІНЬ))
        зм_ = {к: в for к, в in зм.items() if к not in ("MODEL", "MODEL_MOVA")}
        модель = {} if ZHYVA else dict(MODEL="claude-sonnet-5-5", MODEL_MOVA="claude-sonnet-5-5", MODEL_URL=f"http://127.0.0.1:{ПОРТ}/v1")
        env = dict(os.environ, **зм_, **модель,
                   VIDPOVIDI=str(д / "VIDPOVIDI"), ZNIMKY=str(д / "знімки"), ZVIT_OUT=str(д / "вердикти.txt"),
                   CHROMIUM="/opt/pw-browsers/chromium", NODE_PATH="/opt/node-tools/node_modules")
        (д / "код.txt").write_text(f"{SHA} {id_} ПІСЛЯ {('claude-' + ZHYVA + ' (ZHYVA)') if ZHYVA else 'claude-sonnet-5-5'}+{('claude-' + ZHYVA + ' (ZHYVA)') if ZHYVA else 'claude-sonnet-5-5'}\n", encoding="utf-8")
        ч0 = time.time(); п0 = datetime.now(timezone.utc).isoformat()
        cmd = ["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", "/tmp/стенд", "/tmp/pyodide", "3"]
        with open(д / "лог.txt", "w", encoding="utf-8") as л:
            rc = subprocess.run(cmd, cwd=КОРІНЬ, env=env, stdout=л, stderr=subprocess.STDOUT).returncode
        ч1 = time.time()
        ціна = лічба_жива(д) if ZHYVA else лічба_сервера(журнал, ч0, ч1)
        рез = {"початок": п0, "кінець": datetime.now(timezone.utc).isoformat(), "sha": SHA, "сцена": id_, "прохід": прох, "режим": режим,
               "rc": rc, "секунд": round(ч1 - ч0), "змінні": {к: зм[к] for к in зм if к not in ("CHAT_TEXT",)}, "claude_p": ціна}
        (д / "результат.json").write_text(json.dumps(рез, ensure_ascii=False, indent=1), encoding="utf-8")
        with open(ТЕКА / "done.txt", "a", encoding="utf-8") as f:
            f.write(json.dumps({"сцена": id_, "прохід": прох, "rc": rc, "секунд": рез["секунд"], "час": рез["кінець"], **ціна}, ensure_ascii=False) + "\n")
    if сервер: сервер.terminate()


if __name__ == "__main__":
    main()
