"""Прицільні проби незміненого приладу PR #2368; аргумент — дерево його голови."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    корінь = Path(sys.argv[1]).resolve()
    шлях = корінь / "джерела/прилади/корінь_річ_запис_речі.py"
    spec = importlib.util.spec_from_file_location("прилад2368", шлях)
    прилад = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(прилад)
    реєстр = прилад.Реєстр(str(корінь))
    початок = 'import json\nдані=json.load(open("каталог.json"))\nfor р in дані:\n'
    документ = 'import json\nfrom bs4 import BeautifulSoup\npage=BeautifulSoup(html,"html.parser")\n'
    записати = '\njson.dump([р],open("каталог.json","w"))\n'
    js = 'const items=await (await fetch("catalog.json")).json(); for(const r of items){'
    допоміжна = 'import json\ndef тип_зі_слів(текст):\n    return "coat" if "coat" in текст else "dress_generic"\nдані=json.load(open("каталог.json"))\nfor р in дані:\n    р["тип"]=тип_зі_слів(р["назва"])\n'
    проби = [
        ("тип зі слів", "py", початок + '    р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n', {1, 3}),
        ("поле талія", "py", початок + '    р["талія"]="пух" if "пух" in р["опис"] else "без утеплення"\n', {1, 3}),
        ("поле склад", "py", початок + '    р["склад"]="пух" if "пух" in р["опис"] else "без утеплення"\n', {1, 3}),
        ("одноключовий офер у каталозі", "py", 'import json\nофери=json.load(open("каталог.json"))\nофери.append({"тип":"never_registered"})\n', {2}),
        ("JS дужки назва", "js", js + 'r.тип=r["назва"].includes("coat")?"coat":"dress_generic";}', {1, 3}),
        ("JS крапка назва", "js", js + 'r.тип=r.назва.includes("coat")?"coat":"dress_generic";}', {1, 3}),
        ("JS дужки title", "js", js + 'r.тип=r["title"].includes("coat")?"coat":"dress_generic";}', {1, 3}),
        ("JS крапка title", "js", js + 'r.тип=r.title.includes("coat")?"coat":"dress_generic";}', {1, 3}),
        ("весь документ до каталогу", "py", документ + 'р={"назва":page.get_text()}\n' + записати, {4}),
        ("body до каталогу", "py", документ + 'р={"назва":page.select_one("body").get_text()}\n' + записати, {4}),
        ("вузол товару до каталогу", "py", документ + 'р={"назва":page.select_one("#product").get_text()}\n' + записати, set()),
        ("evaluate до каталогу", "py", 'import json\nр={"назва":сторінка.evaluate("document.body.innerText")}\n' + записати, {4}),
        ("опис завдання моделі", "py", документ + 'завдання={"інструкція":page.get_text()}\nмодель(завдання)\n', set()),
        ("координати рамки", "py", 'рамка={"верх":10,"низ":20}\n', set()),
        ("службовий JSON", "js", 'const r=await (await fetch("/api/task")).json(); r.тип="never_registered";', set()),
        ("каталог з іншим іменем", "py", початок.replace('каталог.json', 'offers.json') + '    р["тип"]="coat" if "coat" in р["назва"] else "dress_generic"\n', {1, 3}),
        ("допоміжна з одним викликом", "py", допоміжна, {1, 3}),
        ("допоміжна з шістьма викликами", "py", допоміжна + '\n'.join('тип_зі_слів("службове")' for _ in range(5)) + '\n', {1, 3}),
    ]
    with tempfile.TemporaryDirectory(prefix="проби2368-", dir=os.environ.get("TMP")) as тека:
        for назва, мова, код, очікувані in проби:
            if мова == "py":
                мод = прилад.розібрати_py("джерела/контроль.py", код)
            else:
                файл = Path(тека) / "контроль.js"
                файл.write_text(код, encoding="utf8")
                out = subprocess.run(["node", "--expose-internals", str(шлях.with_name("корінь_річ_запис_речі_js.js")), str(файл)], capture_output=True, encoding="utf8", check=True)
                мод = прилад.розібрати_js("джерела/показ/контроль.js", json.loads(out.stdout)[str(файл)])
            аналіз = прилад.Аналіз([мод], реєстр)
            аналіз.пройти()
            місця = прилад.обчислити(аналіз)
            пункти = {п for ф, р, п in місця}
            print(json.dumps({"проба": назва, "код": код, "очікувані_пункти": sorted(очікувані), "пункти": sorted(пункти), "збіг": пункти == очікувані, "місця": [{"рядок": р, "пункт": п, "чому": ч} for (ф, р, п), ч in sorted(місця.items())]}, ensure_ascii=False))


if __name__ == "__main__":
    головна()
