"""Зберігає відповіді локального API й перевіряє контекст обох моделей до прогону."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ЗБІРКА = КОРІНЬ.parent / "tmp/збірка"
SHA = "29c44a0c8fcb0dc1dbc6eb8d03cb8a7f242c3900"
журнал = {"час_utc": datetime.now(timezone.utc).isoformat(), "запити": []}


def api(шлях="", тіло=None):
    url = "http://127.0.0.1:1234/api/v1/models" + шлях
    запит = urllib.request.Request(url, data=None if тіло is None else json.dumps(тіло).encode(),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(запит, timeout=300) as р:
        відповідь = json.load(р)
        журнал["запити"].append({"url": url, "тіло": тіло, "статус": р.status, "відповідь": відповідь})
    (ТЕКА / "середовище.json").write_text(json.dumps(журнал, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return відповідь


def команда(аргументи, cwd=КОРІНЬ):
    р = subprocess.run(аргументи, cwd=cwd, capture_output=True, encoding="utf-8")
    журнал.setdefault("команди", []).append({"команда": аргументи, "rc": р.returncode,
                                           "stdout": р.stdout, "stderr": р.stderr})
    assert р.returncode == 0, р.stderr
    return р.stdout.strip()


assert команда(["git", "rev-parse", "origin/main"]) == SHA
команда(["git", "merge-base", "--is-ancestor", SHA, "origin/main"])
assert команда(["git", "rev-parse", "HEAD"], ЗБІРКА) == SHA
assert (ЗБІРКА / "build.txt").read_text().strip() == "2133afa881d462226a2e8dc3fca54d5039b81302"
журнал["index_sha256"] = hashlib.sha256((ЗБІРКА / "index.html").read_bytes()).hexdigest()
журнал["змінні"] = {к: os.environ.get(к) for к in ["NODE_OPTIONS", "PYTHONPATH", "NODE_PATH", "TEMP", "TMP"]}
команда(["nvidia-smi"])
моделі = api()["models"]
assert not any(м["loaded_instances"] for м in моделі), "Сервер тримає чужу модель"
for модель, контекст in [("qwen/qwen3.5-9b", 57344), ("mamaylm-gemma-3-12b-it-v2.0", 16384)]:
    assert any(м["key"] == модель for м in моделі), "Нема моделі " + модель
    власний = None
    try:
        р = api("/load", {"model": модель, "context_length": контекст, "parallel": 1, "echo_load_config": True})
        assert р["status"] == "loaded", р
        власний = р["instance_id"]
        екземпляр = next(е for м in api()["models"] if м["key"] == модель
                         for е in м["loaded_instances"] if е["id"] == власний)
        assert екземпляр["config"]["context_length"] == контекст, екземпляр
        assert екземпляр["config"]["parallel"] == 1, екземпляр
        print(модель, json.dumps(екземпляр["config"], ensure_ascii=False), flush=True)
    finally:
        if власний:
            api("/unload", {"instance_id": власний})
assert not any(м["loaded_instances"] for м in api()["models"])
журнал["rc"] = 0
(ТЕКА / "середовище.json").write_text(json.dumps(журнал, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
