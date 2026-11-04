"""Один запис кожного відсутнього порівняльного ДО на заданому коді-предку."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ТИМЧАСОВА = КОРІНЬ.parent / "tmp"
ОТОЧЕННЯ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
    NODE_PATH=r"C:\Users\gemini\kod-shi-test-node\node_modules")
ПЛАН = [
    ("2942", "до-2942", "30173fbb0607e80914be0e1ce3ba43c475d3b392", "ж1_свято_тріада"),
    ("7c", "до-7c", "7c35536c8a3890bf342f81d628d7121320a7204a", "ж4_робота"),
    ("a645", "до-a645", "a645e5ca205c347841c7a2dbe13403868a0004c0", "ж4_робота"),
]
тотожність = json.loads(ТЕКА.joinpath("тотожність-ДО.json").read_text(encoding="utf-8"))
if тотожність.get("рівні_html") is True and тотожність.get("diff_джерел") == []:
    ПЛАН = [крок for крок in ПЛАН if крок[0] != "a645"]
    print("ДО a645 використовує той самий запис, що 7c: джерела й HTML без штампа тотожні", flush=True)
    ТЕКА.joinpath("відповідність-ДО.json").write_text(json.dumps({
        "2957": {"заданий_sha": "a645e5ca205c347841c7a2dbe13403868a0004c0",
            "запис": "ДО/7c/ж4_робота", "доказ_тотожності": "тотожність-ДО.json"},
        "2978": {"заданий_sha": "7c35536c8a3890bf342f81d628d7121320a7204a", "запис": "ДО/7c/ж4_робота"},
        "2942_тріада": {"заданий_sha": "30173fbb0607e80914be0e1ce3ba43c475d3b392", "запис": "ДО/2942/ж1_свято_тріада"},
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for назва, дерево, sha, сцена in ПЛАН:
    збірка = ТИМЧАСОВА / дерево
    html = збірка.joinpath("index.html").read_text(encoding="utf-8")
    штамп = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    if штамп != sha:
        raise RuntimeError(f"Штамп ДО {назва} не збігається: {штамп} != {sha}")
    вихід = ТЕКА / "ДО" / назва / сцена
    команда = [sys.executable, str(ТИМЧАСОВА / "збірка/аудит/проби/записати_сцену.py"),
        str(збірка), r"C:\Users\gemini\pyodide", str(вихід), "--сцена", сцена]
    with ТЕКА.joinpath("команди-ДО.jsonl").open("a", encoding="utf-8") as файл:
        файл.write(json.dumps({"час": datetime.now(timezone.utc).isoformat(), "етап": "ДО",
            "sha": sha, "команда": команда}, ensure_ascii=False) + "\n")
    код = subprocess.run(команда, cwd=КОРІНЬ, env=ОТОЧЕННЯ).returncode
    результат = json.loads(вихід.joinpath("результат.json").read_text(encoding="utf-8"))
    if код not in [0, 1] or результат.get("rc") not in [0, 1]:
        raise RuntimeError(f"ДО {назва} не завершене: rc={код}")
    if результат["sha"] != sha:
        raise RuntimeError("Запис ДО має інший SHA")
    # Штатний записувач пише «ПІСЛЯ» для всіх викликів. Тут позначається фактична роль запису;
    # первісні обміни, відповіді, результат і доказ залишаються незміненими.
    код_текст = вихід.joinpath("код.txt").read_text(encoding="utf-8").replace(" ПІСЛЯ ", " ДО ", 1)
    вихід.joinpath("код.txt").write_text(код_текст, encoding="utf-8")
    вихід.joinpath("роль.json").write_text(json.dumps({"етап": "ДО", "sha": sha,
        "сцена": сцена, "причина": "Сумісного завершеного запису на коді-предку не знайдено"},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with ТЕКА.joinpath("done-ДО.txt").open("a", encoding="utf-8") as файл:
        файл.write(f"{datetime.now(timezone.utc).isoformat()} {назва} {сцена} rc={код}\n")
    subprocess.run(["git", "add", "--", str(ТЕКА.relative_to(КОРІНЬ))], cwd=КОРІНЬ, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Записати порівняльний ДО " + назва + " для " + сцена],
        cwd=КОРІНЬ, check=True)
    print(f"ДО {назва} збережено: rc={код}", flush=True)
