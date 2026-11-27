#!/usr/bin/env python3
"""Пункт 4: 20 запитів складання однієї сцени з тим самим пулом і різним сідом порядку рядків пулу.
Транспорт стенда: `claude -p --model sonnet` із системним рядком `джерела/проби/мова_спільне.py` (ZHYVA=sonnet), як у Н3–Н5.
Запуск з кореня: python3 -I аудит/звіти/стилістка-вибір-з-пулу/проба.py <сід> [сцена/прохід/рядок]  — один виклик, запис проба/<сід>.json
                 ... проба.py --усі — 20 викликів по 4 паралельно."""
import importlib.util, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
сп = importlib.util.spec_from_file_location("попередній", ТЕКА.parent / "крамниці-рівна-черга" / "вимір.py")
П = importlib.util.module_from_spec(сп); sys.modules["попередній"] = П; сп.loader.exec_module(П)
ЗАПИТ = "ж3_кафе_20/1/7"
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, "
             "verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code "
             "fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, no "
             "tools, no questions back.")


def запит_із_запису(ключ=ЗАПИТ):
    сцена, прохід, лінія = ключ.split("/")
    шлях = f"{П.МІСТ}/{сцена}/обміни.jsonl"
    обмін = П.рядки(шлях)[int(лінія) - 1]
    return П.розібрати_json(П.текст_запиту(json.loads(обмін["запит"])))


def промпт(сід, ключ=ЗАПИТ):
    пакет = запит_із_запису(ключ)
    rs = пакет["pool"]["rows"]
    random.Random(сід).shuffle(rs)
    return json.dumps(пакет, ensure_ascii=False, separators=(",", ":"))


def виклик(сід):
    вихід = ТЕКА / "проба" / f"{сід:02d}.json"
    if вихід.exists():
        return
    т0 = time.time()
    р = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                        "--system-prompt", СИСТЕМНИЙ], input=промпт(сід), capture_output=True, text=True, timeout=900,
                       env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
    вихід.parent.mkdir(exist_ok=True)
    вихід.write_text(json.dumps(dict(сід=сід, секунд=round(time.time() - т0, 1), rc=р.returncode, відповідь=р.stdout, помилка=р.stderr[-500:]),
                                ensure_ascii=False) + "\n", encoding="utf-8")
    print(сід, р.returncode, round(time.time() - т0), len(р.stdout), flush=True)


if __name__ == "__main__":
    сіди = range(1, 21) if sys.argv[1] == "--усі" else [int(sys.argv[1])]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(виклик, сіди))
