# -*- coding: utf-8 -*-
"""СТАНДАРТ_КОДУ §4 п.13: параметр, якого функція не читає. Клас — З КОДУ, не з пам'яті:
нема в сигнатурі гілки → МЕРТВИЙ (знято), є з `_` → СТРАХОВКА (свідомо, причина в докстрінгу),
є без `_` → ПРОГАЛИНА (вхід їде, читача нема — названа на дошці, тут не лагодиться).
«Викликачів» — греп по імені в дереві (.py/.js/.html), тож омоніми (`перевірити`) лічаться разом.
Прогін: cd джерела && python3 проби/mertvi_parametry_13.py [база]"""
import ast, os, re, subprocess, sys
ДЖ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(ДЖ)); sys.path.insert(0, ДЖ)
import status
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "399181f"

def нечитані(текст):
    """{(функція, параметр)} тим самим правилом, що `аудит/проби/рв6_стандарт.py`."""
    out = set()
    for x in ast.walk(ast.parse(текст)):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
            вжиті = {y.id for y in ast.walk(x) if isinstance(y, ast.Name)}
            out |= {(x.name, a.arg) for a in x.args.posonlyargs + x.args.args + x.args.kwonlyargs
                    if a.arg not in ("self", "cls") and a.arg not in вжиті}
    return out

ТЕКСТИ = {os.path.join(d, f): open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
          for d, _, fs in os.walk(".") for f in fs if f.endswith((".py", ".js", ".html"))
          and not re.search(r"open-source-stylist|zhnyvarka|__pycache__|[/\\]\.git", d)}
лічба, рядків = {"мертвий": 0, "прогалина": 0, "страховка": 0}, 0
print("модуль.функція · параметр · клас · викликачів · передають (перші три)")
for м in sorted(status.МОДУЛІ_ПРОДУКТУ):
    до = нечитані(subprocess.run(["git", "show", "%s:джерела/%s.py" % (БАЗА, м)],
                                 capture_output=True, text=True, check=True).stdout)
    після = нечитані(open("джерела/%s.py" % м, encoding="utf-8").read())
    for ф, п in sorted(до):
        клас = "страховка" if (ф, "_" + п) in після else "прогалина" if (ф, п) in після else "мертвий"
        лічба[клас] += 1; рядків += 1
        викл = ["%s:%d" % (ш, i + 1) for ш, т in sorted(ТЕКСТИ.items()) for i, р in enumerate(т.splitlines())
                if re.search(r"[.\s=(\[,]%s\s*\(" % re.escape(ф), р) and not р.lstrip().startswith(("def ", "#"))]
        print("%-22s %-28s %-10s %-3d %s" % (м + "." + ф, п, клас, len(викл), ", ".join(викл[:3]) or "—"))
print("ДО (%s) нечитаних %d · знято з сигнатур %d · лишилось %d: прогалин %d + страховок %d з `_` · "
      "МЕРТВИХ У СИГНАТУРАХ 0" % (БАЗА, рядків, лічба["мертвий"], лічба["прогалина"] + лічба["страховка"],
                                  лічба["прогалина"], лічба["страховка"]))
