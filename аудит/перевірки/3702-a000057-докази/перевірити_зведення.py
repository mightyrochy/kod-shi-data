"""Прицільна перевірка #3702 без моделей.

python перевірити_зведення.py <дерево PR> <колізія> <дим> <тека доказів>
Перші дві теки результатів створюють відтворити.js і дим_рук.js.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

дерево, колізія, дим, докази = map(lambda p: Path(p).resolve(), sys.argv[1:])
звести = дерево / "аудит/проби/живий-як-людина-1/стенд/звести.py"
докази.mkdir(parents=True, exist_ok=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"  # журнал стенда записаний у UTF-8, як у Linux автора


def зведення(тека):
    return subprocess.check_output(
        [sys.executable, str(звести), "руки"], cwd=тека, encoding="utf-8"
    )


for назва, тека, ситуація in [("колізія", колізія, "с1_проба"), ("дим", дим, "с0_дим")]:
    запис = тека / "службове" / ситуація / "руки.jsonl"
    shutil.copyfile(запис, докази / f"{назва}-руки.jsonl")
    текст = зведення(тека)
    (докази / f"{назва}-зведення.md").write_text(текст, encoding="utf-8")
    assert "| 4242 |" in текст and "K-CRA-01" in текст
    assert "hand_2_broken=K-SIL-03" not in текст
    if назва == "колізія":
        assert "| с1 · 1 | 4242 | 3142 | 3 | 1 | 4 | 2 (код з поломкою) |" in текст
    else:
        assert "| с0 · 2 | 777 | 4213 |" in текст
        assert "завантажено: 3, силует (кадри вичерпано): 1" in текст
    print(f"ТАК {назва}: зведення зберігає метадані А")

with tempfile.TemporaryDirectory(prefix="review3702-", dir=os.environ["TEMP"]) as тимч:
    тека = Path(тимч)
    службове = тека / "службове/с1_проба"
    службове.mkdir(parents=True)
    записи = [json.loads(л) for л in (докази / "колізія-руки.jsonl").read_text(encoding="utf-8").splitlines()]
    чужий = copy.deepcopy(записи[0])
    чужий.update(готово=False, сід=1)
    чужий["поломка_руки_2"] = {"діагноз": ["control · hand_2_broken=K-SIL-03"], "що": "чужа поломка"}
    записи.append(чужий)
    файл = службове / "руки.jsonl"
    файл.write_text("".join(json.dumps(з, ensure_ascii=False) + "\n" for з in записи), encoding="utf-8")
    текст = зведення(тека)
    assert "| с1 · 1 | 4242 | 3142 |" in текст
    assert "K-CRA-01" in текст and "K-SIL-03" not in текст
    shutil.copyfile(файл, докази / "незавершене-руки.jsonl")
    (докази / "незавершене-зведення.md").write_text(текст, encoding="utf-8")
    print("ТАК готово=false: чужі сід і поломка не стирають метадані А")

    база = тека / "звести_база.py"
    база.write_bytes(subprocess.check_output([
        "git", "show", "87bc30d5ca14458e73cda5c0072edee0ae662f76:аудит/проби/живий-як-людина-1/стенд/звести.py"
    ]))
    робоча = звести.parent
    результати = []
    for назва, скрипт in [("база", база), ("голова", звести)]:
        п = subprocess.run([sys.executable, str(скрипт)], cwd=робоча, capture_output=True, encoding="utf-8")
        (докази / f"ціна-{назва}.txt").write_text(
            f"команда: {sys.executable} {скрипт}\nтека: {робоча}\nкод: {п.returncode}\n{п.stdout}{п.stderr}", encoding="utf-8"
        )
        print(f"Режим ціни, {назва}: код {п.returncode}; " + (п.stderr.splitlines()[-1] if п.stderr else "успіх"))
        assert п.returncode == 0
        результати.append(п.stdout)
    assert результати[0] == результати[1]
    print("ТАК без аргументу: таблиця ціни тотожна базі PR")

shutil.copyfile(колізія / "390x844.png", докази / "390x844.png")
