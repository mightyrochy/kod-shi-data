"""Друкує факти приладу PR #2368 на малих фрагментах без зміни реалізації."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    """Імпортує прилад із переданого дерева й перевіряє межі класу."""
    корінь = Path(sys.argv[1]).resolve()
    шлях = корінь / "джерела/прилади/корінь_річ_запис_речі.py"
    спец = importlib.util.spec_from_file_location("прилад2368", шлях)
    прилад = importlib.util.module_from_spec(спец)
    спец.loader.exec_module(прилад)
    реєстр = прилад.Реєстр(str(корінь))
    початок = 'import json\nдані=json.load(open("каталог.json"))\nfor р in дані:\n'
    документ = 'from bs4 import BeautifulSoup\npage=BeautifulSoup(html,"html.parser")\n'
    проби = [
        ("тип зі слів", "py", початок + '    р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n'),
        ("талія зі слів", "py", початок + '    р["талія"]="пух" if "пух" in р["опис"] else "без утеплення"\n'),
        ("одноключовий офер", "py", 'import json\nофери=json.load(open("каталог.json"))\nофери.append({"тип":"never_registered"})\n'),
        ("body", "py", документ + 'р={"назва":page.select_one("body").get_text()}\n'),
        ("вузол товару", "py", документ + 'р={"назва":page.select_one("#product").get_text()}\n'),
        ("корінь документа", "py", документ + 'р={"назва":page.get_text()}\n'),
        ("evaluate", "py", 'р={"назва":сторінка.evaluate("document.body.innerText")}\n'),
        ("JS крапка", "js", 'const items=JSON.parse(fetch("catalog.json")); for(const r of items){r.тип=r.назва.includes("coat")?"coat":"dress_generic";}'),
        ("рамка", "py", 'рамка={"верх":0.1,"низ":0.8}\nif "верх" in рамка: print(рамка["низ"])\n'),
        ("кеш", "py", 'import json\nкеш=json.load(open("cache.json"))\nif "coat" in кеш.get("текст", ""): print("так")\n'),
        ("кодове поле тип", "py", початок + '    р["тип"]="never_registered"\n'),
        ("кодове поле талія", "py", початок + '    р["талія"]="never_registered"\n'),
        ("кодова група слот", "py", 'import json\nГРУПА=("top","bottom")\nдані=json.load(open("каталог.json"))\nfor р in дані:\n    if р["слот"] in ГРУПА: print(р)\n'),
        ("кодова група талія", "py", 'import json\nГРУПА=("high","mid","low")\nдані=json.load(open("каталог.json"))\nfor р in дані:\n    if р["талія"] in ГРУПА: print(р)\n'),
        ("кодова група талія продукту", "py", 'import json\nГРУПА=("belt","wrap","elastic_waist","fixed_waist")\nдані=json.load(open("каталог.json"))\nfor р in дані:\n    if р["талія"] in ГРУПА: print(р)\n'),
        ("шлях через defaultdict", "py", 'import json\nfrom collections import defaultdict\nдані=json.load(open("каталог.json"))\nгрупи=defaultdict(list)\nfor р in дані:\n    групи[р["слот"]].append(р)\nfor слот, речі in групи.items():\n    for р in речі:\n        р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n'),
        ("блоки відповіді моделі", "js", 'const data=response.json(); const text=(data.content||[]).map(b=>b.type==="text"?b.text:"").filter(Boolean).join("\\n");'),
        ("довге слово", "py", початок + '    р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n'),
        ("коротке слово", "py", початок + '    р["тип"]="coat" if "їж" in р["назва"] else "dress_generic"\n'),
        ("службовий запит моделі", "py", 'from bs4 import BeautifulSoup\np=BeautifulSoup(html,"html.parser")\nзапит={"інструкція":p.select_one("#product").get_text().replace("coat", "dress")}\nмодель(запит)\n'),
    ]
    with tempfile.TemporaryDirectory(prefix="перевірка2368-", dir=os.environ.get("TMP")) as тека:
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
            аналіз = прилад.Аналіз([модуль], реєстр)
            аналіз.пройти()
            місця = прилад.обчислити(аналіз)
            print(json.dumps({"проба": назва, "місць": len({(ф, р) for ф, р, п in місця}),
                              "пункти": sorted({п for ф, р, п in місця}),
                              "місця": [[р, п, ч] for (ф, р, п), ч in sorted(місця.items())]}, ensure_ascii=False))


if __name__ == "__main__":
    головна()
