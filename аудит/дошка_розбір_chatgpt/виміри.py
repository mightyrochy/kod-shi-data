#!/usr/bin/env python3
"""Друкує факти чинного коду; не змінює джерел, дошки чи каталогу.

python3 аудит/дошка_розбір_chatgpt/виміри.py > /tmp/д1-виміри.json
Це діагностика Д.1, не новий гейт продукту. Моделей і мережі не викликає.
"""
import ast
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
sys.dont_write_bytecode = True


def виконати():
    """Виміряти механізми на функціях і поточному каталозі, позначивши синтетичні входи."""
    сл = importlib.import_module("фід_слот")
    др = importlib.import_module("дріт_моделі")
    кр = importlib.import_module("каталог_розбір")
    кк = importlib.import_module("каталог_коди")
    мш = importlib.import_module("мовний_шар")
    ок = importlib.import_module("оцінка_образу")
    фк = importlib.import_module("фід_кадр_колір")
    в = importlib.import_module("verify")
    вих = {
        "sha_джерел": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=КОРІНЬ, text=True).strip(),
        "синтетичні_входи": {},
        "статичні_факти": {},
    }
    с = вих["синтетичні_входи"]
    с["8240_деталі_рядком"] = др._деталі("structured")
    с["8240_деталі_списком"] = др._деталі(["structured"])
    с["6571_без_попереднього_місця"] = мш._ошатність_плиткою({"formality": {"from": 5, "to": 7}})
    с["6571_з_місцем"] = мш._ошатність_плиткою(
        {"formality": {"from": 5, "to": 7}, "place": "office_corporate"})
    # Ключі частин читаємо з модуля: не підмінюємо контракт гіпотезою про назву ключа.
    частини = кр.частини_тексту({"name": "СУКНЯ", "title": "СУКНЯ", "назва": "СУКНЯ"})
    с["421_ключі_частин"] = list(частини)
    с["421_підрядок_не_перевіряє_значення"] = {
        "цитата": "СУКНЯ",
        "де": кр._де_тримається("СУКНЯ", {к: ["СУКНЯ"] for к in кр.ЧАСТИНИ}),
        "межа": "Ця функція не одержує код, тому не може перевірити його семантику.",
    }
    с["8141_одна_виміряна_річ"] = ок._суперечить(
        "colors_together", ["ф1"],
        {"речі": [{"ід": "ф1", "вимір": {"lab": [50, 0, 0]}}]}
    )
    с["266_одна_сімя_без_узгодженого_lab"] = фк.узгоджений(
        "синій", (95, 0, 0), в.сім_я_слова("синій")
    )
    # Функція сама викликає чистку, тому обидві версії архіву — лише у тимчасовій теці.
    фід = importlib.import_module("фід_каталог")
    зразок = '<yml_catalog><shop><offers><offer id="1"><name>Сукня {}</name></offer></offers></shop></yml_catalog>'
    with tempfile.TemporaryDirectory(prefix="д1-каталог-") as т:
        файл = Path(т) / "каталог_повний.xml"
        архів = Path(str(файл) + ".gz")
        архів.write_bytes(gzip.compress(зразок.format("А").encode()))
        фід.каталог_на_диску(str(файл))
        до = файл.read_bytes()
        архів.write_bytes(gzip.compress(зразок.format("Б").encode()))
        фід.каталог_на_диску(str(файл))
        після = файл.read_bytes()
        с["8101_заміна_архіву"] = {"змінився_xml": до != після, "містить_нову_назву": "Сукня Б" in після.decode()}
    ст = вих["статичні_факти"]
    показ = (КОРІНЬ / "джерела/показ.html").read_text()
    ремонт = (КОРІНЬ / "джерела/вердикт_моделі.py").read_text()
    ст["7310_нуль_години_замінюється_на_11"] = "година:parseInt($('сц-година').value)||11" in показ
    ст["8512_CLAUDE_байтів"] = (КОРІНЬ / "CLAUDE.md").stat().st_size
    ст["8620_скрипт_sam_існує"] = (КОРІНЬ / "джерела/запуск_sam_8000.ps1").exists()
    ст["8610_fromBase64_є"] = "Uint8Array.fromBase64" in показ
    ст["6785_згадка_Do_not_put_it_under_answer"] = "Do not put it under" in ремонт
    ст["1690_файл_розбору"] = кк.шлях()
    ст["1690_записів_розбору"] = len(кк.читати())
    # Каталог читається сирим у тимчасовій теці. Одиниця — запис, не унікальний дизайн.
    архів = КОРІНЬ / "каталог_повний.xml.gz"
    фр = importlib.import_module("фід_розбір")
    with tempfile.TemporaryDirectory(prefix="д1-фід-") as т:
        шлях = Path(т) / "сирий.xml"
        шлях.write_bytes(gzip.decompress(архів.read_bytes()))
        офери = фр.офери_фіду(str(шлях))
        факти = []
        for о in офери:
            ід = str(о.get("id") or о.get("ід") or "")
            назва = о.get("назва") or ""
            if any(х in ід for х in ["ж-15745@", "ж-16895@", "ж-08403@", "ж-07448@"]):
                факти.append({"ід": ід, "назва": назва, "слот_функції": сл.слот(о), "тип_функції": сл.тип_речі(о)})
        вих["каталог"] = {
            "sha256_gz": hashlib.sha256(архів.read_bytes()).hexdigest(),
            "сирих_записів": len(офери), "вибрані_записи": факти,
        }
    # Показуємо конкретну кількість входів складного вузла без запуску продукту.
    дерево = ast.parse((КОРІНЬ / "джерела/міст_відповіді.py").read_text())
    ст["від_моделі_рядків"] = next(
        ф.end_lineno - ф.lineno + 1 for ф in дерево.body
        if isinstance(ф, ast.FunctionDef) and ф.name == "від_моделі"
    )
    print(json.dumps(вих, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    виконати()
