"""Відтворює прицільні проби приладу з призначеного дерева PR #2330."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    """Імпортує перевірюваний прилад і друкує факти на малих фрагментах."""
    корінь = Path(sys.argv[1]).resolve()
    шлях = корінь / "джерела/прилади/корінь_річ_запис_речі.py"
    специфікація = importlib.util.spec_from_file_location("прилад2330", шлях)
    прилад = importlib.util.module_from_spec(специфікація)
    специфікація.loader.exec_module(прилад)
    реєстр = прилад.Реєстр(str(корінь))
    початок = 'import json\nдані=json.load(open("каталог.json"))\nfor р in дані:\n'
    документ = 'from bs4 import BeautifulSoup\npage=BeautifulSoup(html,"html.parser")\n'
    проби = [
        ("тип зі слів", "py", початок + '    р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n'),
        ("поле талія", "py", початок + '    р["талія"]="пух" if "пух" in р["опис"] else "без утеплення"\n'),
        ("поле склад", "py", початок + '    р["склад"]="пух" if "пух" in р["опис"] else "без утеплення"\n'),
        ("JS дужки", "js", 'const items=fetch("catalog.json"); for(const r of items){r["тип"]=r["назва"].includes("coat")?"coat":"dress_generic";}'),
        ("JS крапка", "js", 'const items=fetch("catalog.json"); for(const r of items){r.тип=r.назва.includes("coat")?"coat":"dress_generic";}'),
        ("весь документ", "py", документ + 'р={"назва":page.get_text(),"тип":"coat"}\n'),
        ("один ключ", "py", 'р={"тип":"never_registered"}\n'),
        ("два ключі", "py", 'р={"тип":"never_registered","назва":"пальто"}\n'),
        ("body", "py", документ + 'р={"назва":page.select_one("body").get_text(),"тип":"coat"}\n'),
        ("товарний блок", "py", документ + 'р={"назва":page.select_one("#product").get_text(),"тип":"coat"}\n'),
        ("одноключовий офер у каталозі", "py", 'import json\nофери=json.load(open("каталог.json"))\nофери.append({"тип":"never_registered"})\n'),
    ]
    with tempfile.TemporaryDirectory(prefix="перевірка2330-", dir=os.environ.get("TMP")) as тека:
        for назва, мова, код in проби:
            if мова == "py":
                модуль = прилад.розібрати_py("джерела/контроль.py", код)
            else:
                файл = Path(тека) / "контроль.js"
                файл.write_text(код, encoding="utf8")
                результат = subprocess.run(
                    ["node", "--expose-internals", str(шлях.with_name("корінь_річ_запис_речі_js.js")), str(файл)],
                    capture_output=True, encoding="utf8", check=True,
                )
                дерево = json.loads(результат.stdout)[str(файл)]
                модуль = прилад.розібрати_js("джерела/показ/контроль.js", дерево)
            рушій = прилад.Рушій([модуль], реєстр)
            аналіз = прилад.Аналіз(рушій, реєстр)
            аналіз.виконати()
            місця = прилад.обчислити(аналіз, str(корінь)).м
            print(json.dumps({"проба": назва, "місць": len({(ф, р) for ф, р, п in місця}),
                              "пункти": sorted({п for ф, р, п in місця})}, ensure_ascii=False))


if __name__ == "__main__":
    головна()
