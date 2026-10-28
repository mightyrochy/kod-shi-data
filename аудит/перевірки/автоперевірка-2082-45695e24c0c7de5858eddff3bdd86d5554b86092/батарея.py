"""Повтор батареї голови PR 2082 з повними журналами поза репозиторієм."""
import json
import os
import pathlib
import subprocess
import sys
import time


def main():
    """Виконати всі команди послідовно й зберегти коди та дослівні підсумки."""
    дерево = pathlib.Path(sys.argv[1])
    журнали = pathlib.Path(sys.argv[2])
    журнали.mkdir(parents=True, exist_ok=True)
    середовище = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1",
                     NODE_PATH=str(pathlib.Path.cwd() / "джерела/node_modules"))
    for ключ in ("E2_SOURCES", "MODEL", "MODEL_MOVA"):
        середовище.pop(ключ, None)
    джерело = дерево / "аудит/проби/Е2-ремонт-шар/батарея.json"
    результати = []
    for номер, запис in enumerate(json.loads(джерело.read_text(encoding="utf-8")), 1):
        команда = запис["команда"].replace("\\", "/")
        арг = команда.split()
        if арг[0] == "python":
            арг[0:1] = [sys.executable, "-X", "utf8"]
        робоча = дерево if арг[1:2] == ["аудит/проби/ремонт_шар.js"] else дерево / "джерела"
        початок = time.monotonic()
        print(f"{номер}: {команда}", flush=True)
        with (журнали / f"{номер:02}.txt").open("w", encoding="utf-8") as ф:
            р = subprocess.run(арг, cwd=робоча, env=середовище, stdout=ф, stderr=subprocess.STDOUT)
        текст = (журнали / f"{номер:02}.txt").read_text(encoding="utf-8")
        кінець = текст.splitlines()[-4:]
        результати.append(dict(команда=команда, код=р.returncode,
                              секунд=round(time.monotonic() - початок, 1), кінець=кінець))
        print(f"код {р.returncode}: " + " / ".join(кінець), flush=True)
    підсумок = pathlib.Path(__file__).with_name("батарея.json")
    підсумок.write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    помилок = sum(р["код"] != 0 for р in результати)
    print(f"Команд: {len(результати)}; червоних: {помилок}", flush=True)
    return bool(помилок)


if __name__ == "__main__":
    sys.exit(main())
