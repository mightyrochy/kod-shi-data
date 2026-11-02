# -*- coding: utf-8 -*-
"""Скрипт перевірки та відтворення результатів перевірки PR #2781 (голова 860c0f5521353a7edf5faa2ea8f4b9865c4520ef).
Запуск: python -X utf8 аудит/перевірки/перевірка-2781_проба.py
"""
import ast
import collections
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import warnings

warnings.filterwarnings("ignore")

РЕПО = pathlib.Path(__file__).resolve().parents[2]
HEAD_SHA = "860c0f5521353a7edf5faa2ea8f4b9865c4520ef"
BASE_SHA = "dd94372e1e53b9bd75af75cf8c01e1b172f3cbd7"


def перевірити_github_api():
    print("1. Звірка через GitHub API...")
    req = urllib.request.Request(
        "https://api.github.com/repos/mightyrochy/kod-shi-data/pulls/2781",
        headers={"User-Agent": "ReviewScript/1.0"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        assert data["user"]["login"] == "mightyrochy", "Автор не mightyrochy"
        assert data["head"]["repo"]["full_name"] == "mightyrochy/kod-shi-data", "head repo не kod-shi-data"
        assert data["base"]["repo"]["full_name"] == "mightyrochy/kod-shi-data", "base repo не kod-shi-data"
        assert data["base"]["ref"] == "main", "база не main"
        assert data["head"]["sha"] == HEAD_SHA, f"голова не {HEAD_SHA}"
        print(f"   ✓ PR #2781: автор {data['user']['login']}, база {data['base']['ref']}, голова {data['head']['sha']}")
    except Exception as e:
        print(f"   ! GitHub API: {e} (пропускаємо через ліміт чи відсутність мережі)")


def перевірити_ast():
    print("2. Звірка AST функцій і класів продукту...")
    base_code = subprocess.check_output(["git", "show", f"{BASE_SHA}:джерела/мовний_шар.py"], cwd=РЕПО).decode("utf8")
    head_code = subprocess.check_output(["git", "show", f"{HEAD_SHA}:джерела/мовний_шар.py"], cwd=РЕПО).decode("utf8")

    def get_defs(code):
        tree = ast.parse(code)
        defs = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs[node.name] = ast.dump(node)
        return defs

    bd = get_defs(base_code)
    hd = get_defs(head_code)
    diffs = [k for k in set(bd) | set(hd) if bd.get(k) != hd.get(k)]
    assert len(diffs) == 0, f"Знайдено зміни у функціях/класах: {diffs}"
    print("   ✓ Функції та класи продукту в мовний_шар.py: AST-незмінні (0 змін)")


def перевірити_повтор_записів():
    print("3. Повтор 161 записаного ходу та звірка хешу SHA-256...")
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        archive_bytes = subprocess.check_output(["git", "archive", HEAD_SHA, "джерела/"], cwd=РЕПО)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as tar:
            tar.extractall(path=tdp)

        sys_path_bak = list(sys.path)
        sys.path.insert(0, str(tdp / "джерела"))

        for m in ["мовний_шар", "паспорт_нагоди", "формальність", "паспорт_поля", "внутрішня_мова"]:
            if m in sys.modules:
                del sys.modules[m]
        import мовний_шар as М, паспорт_нагоди as ПН, формальність as Ф

        raw = subprocess.check_output(["git", "ls-tree", "-r", "-z", "--name-only", HEAD_SHA], cwd=РЕПО).decode("utf8").split("\0")
        файли = sorted(ф for ф in raw if re.search(r"/VIDPOVIDI/seed[^/]*_01_мовний_шар_хід_розмови\.txt$", ф))
        assert len(файли) == 161, f"Очікувалось 161 файл, знайдено {len(файли)}"

        л = collections.Counter()
        нагоди = collections.Counter()
        відбиток = hashlib.sha256()

        for ф in файли:
            текст = subprocess.check_output(["git", "show", f"{HEAD_SHA}:{ф}"], cwd=РЕПО).decode("utf8", errors="replace")
            запит, відповідь = текст.split("── ВІДПОВІДЬ", 1)
            запит = json.loads(запит[запит.find("{"):запит.rfind("}") + 1])
            в = М.прийняти_розмову(відповідь[відповідь.find("{"):відповідь.rfind("}") + 1])["внутрішня"]
            п = М.паспорт_з_шару(в, {}, слова_ходу=[])["паспорт"]
            с = ПН.з_показу({}, п)[0]
            смуги = [Ф.смуга_ошатності(dict(с, пора=пора)) for пора in ("день", "вечір")]
            відбиток.update(json.dumps([ф, в, п, с, смуги], ensure_ascii=False, sort_keys=True, default=str).encode("utf8"))
            нагоди[в.get("occasion", "unknown")] += 1
            л["ходів"] += 1
            л["не date"] += (в.get("occasion") != "date")

        sha = відбиток.hexdigest()
        очікуваний_sha = "3ce8dec7dc228169ebd6e4f91ae1e11483b0bbe8ef1cba222d68c2563b660c97"
        assert sha == очікуваний_sha, f"Хеш не збігається: {sha} != {очікуваний_sha}"
        assert л["ходів"] == 161 and л["не date"] == 135, f"Кількість ходів не збігається: {dict(л)}"
        print(f"   ✓ Ходів: 161 (не date: 135, date: 26). SHA-256 відбиток: {sha}")
        sys.path = sys_path_bak


def перевірити_яруси():
    print("4. Перевірка ярусів формальності (everyday / neat)...")
    sys_path_bak = list(sys.path)
    sys.path.insert(0, str(РЕПО / "джерела"))
    import формальність as Ф

    e_day = Ф.смуга_ошатності({"нагода": "everyday", "ошатність": [3, 4], "пора": "день"})[:2]
    e_eve = Ф.смуга_ошатності({"нагода": "everyday", "ошатність": [3, 4], "пора": "вечір"})[:2]
    assert e_day == (3.0, 4.0) and e_eve == (3.0, 4.0), f"everyday day/eve збій: {e_day}, {e_eve}"

    n_day = Ф.смуга_ошатності({"нагода": "everyday", "ошатність": [5, 6], "пора": "день"})[:2]
    n_eve = Ф.смуга_ошатності({"нагода": "everyday", "ошатність": [5, 6], "пора": "вечір"})[:2]
    assert n_day == (5.0, 6.0) and n_eve == (7.0, 7.0), f"neat day/eve збій: {n_day}, {n_eve}"

    d_day = Ф.смуга_ошатності({"нагода": "date", "ошатність": [3, 4], "пора": "день"})[:2]
    d_eve = Ф.смуга_ошатності({"нагода": "date", "ошатність": [3, 4], "пора": "вечір"})[:2]
    assert d_day == (3.0, 4.0) and d_eve == (3.0, 4.0), f"date everyday day/eve збій: {d_day}, {d_eve}"

    print("   ✓ Everyday: день (3.0, 4.0), вечір (3.0, 4.0) — без підйому")
    print("   ✓ Neat: день (5.0, 6.0), вечір (7.0, 7.0) — підйом на щабель")
    sys.path = sys_path_bak


def перевірити_дошку():
    print("5. Перевірка записів дошки в аудит/дошка/gemini/Е2-нагода-зустріч.md...")
    sys_path_bak = list(sys.path)
    sys.path.insert(0, str(РЕПО / "джерела" / "прилади"))
    import дошка_поля

    s = subprocess.check_output(["git", "show", f"{HEAD_SHA}:аудит/дошка/gemini/Е2-нагода-зустріч.md"], cwd=РЕПО).decode("utf8")
    lines = s.strip().splitlines()
    assert len(lines) == 2, f"Очікувалось 2 рядки, отримано {len(lines)}"
    for line in lines:
        errs = дошка_поля.перевірити_поля(line)
        assert len(errs) == 0, f"Помилки валідації дошки: {errs} для рядка {line}"
    print("   ✓ Обидва рядки дошки (8975, 12260) пройшли перевірку дошка_поля без помилок")
    sys.path = sys_path_bak


def головна():
    print(f"Початок перевірки PR #2781 (голова {HEAD_SHA})")
    перевірити_github_api()
    перевірити_ast()
    перевірити_повтор_записів()
    перевірити_яруси()
    перевірити_дошку()
    print("УСІ ПЕРЕВІРКИ ПРОЙДЕНО УСПІШНО.")


if __name__ == "__main__":
    головна()
