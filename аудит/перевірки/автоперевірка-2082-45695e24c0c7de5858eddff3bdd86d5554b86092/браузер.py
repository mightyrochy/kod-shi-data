"""Перевірити зібрану голову PR 2082 та зберегти знімки справжнього Chromium."""
import json
import os
import pathlib
import subprocess
import sys
import time


def main():
    """Дочекатися перевірки артефакта й стенда, зберігши фактичні результати."""
    дерево, збірка, тека = map(pathlib.Path, sys.argv[1:4])
    тека.mkdir(parents=True, exist_ok=True)
    середовище = dict(os.environ, NODE_PATH=str(pathlib.Path.cwd() / "джерела/node_modules"),
                     CHROMIUM="C:/Users/gemini/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe",
                     FOTO="1", ZNIMKY=str(тека / "знімки"), PYTHONIOENCODING="utf-8")
    for ключ in ("MODEL", "MODEL_MOVA", "ZHYVA", "E2_SOURCES"):
        середовище.pop(ключ, None)
    результати = []
    for назва, команда in (
        ("показ-артефакта", ["node", "джерела/тест_показу.js", str(збірка / "index.html")]),
        ("стенд", ["node", "аудит/проби/рв6_стенд.js", "http://127.0.0.1:8765",
                   str(збірка), "C:/Users/gemini/pyodide", "3"]),
    ):
        print(назва, flush=True)
        початок = time.monotonic()
        with (тека / (назва + ".txt")).open("w", encoding="utf-8") as ф:
            р = subprocess.run(команда, cwd=дерево, env=середовище, stdout=ф, stderr=subprocess.STDOUT)
        текст = (тека / (назва + ".txt")).read_text(encoding="utf-8")
        кінець = текст.splitlines()[-12:]
        результати.append(dict(команда=команда, код=р.returncode,
                              секунд=round(time.monotonic() - початок, 1), кінець=кінець))
        print(f"код {р.returncode}: " + " / ".join(кінець), flush=True)
    pathlib.Path(__file__).with_name("браузер.json").write_text(
        json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    return any(р["код"] for р in результати)


if __name__ == "__main__":
    sys.exit(main())
