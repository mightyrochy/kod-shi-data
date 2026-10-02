# -*- coding: utf-8 -*-
"""ПЛИТ-1 (рядки 752, 754): скільки нагод довідника стоять плиткою на аркуші «Нагода», і що паспорт дістає
з ходу плиток БЕЗ розмови на кожній плитці (ошатність — число моделі, година й звідки вона). Без аргументів —
лише довідник; з `<тека зі зібраним index.html> <тека Pyodide>` — ще й стенд-заглушка `PLYTKA=всі`
(`аудит/проби/рв6_стенд.js`): той самий дотик, що в жінки, і той самий шов `паспортШаромП`.
Запуск із `джерела`; ганяти на двох SHA й порівняти."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import паспорт_нагоди as ПН
н = ПН.довідник()["нагоди"]
плитки = [р["ключ"] for р in н if р["плитка"]]
print("нагод у довіднику: %d · плиткою на аркуші: %d · ходових: %d" % (
    len(н), len(плитки), sum(1 for р in н if р.get("ходова", р["плитка"]))))
print("без плитки:", ", ".join(р["ключ"] for р in н if not р["плитка"]) or "—")
if len(sys.argv) < 3:
    sys.exit(0)
корінь = os.path.dirname(sys.path[0])
env = dict(os.environ, PLYTKA="всі", NODE_PATH=os.path.join(sys.path[0], "node_modules"),
           CHROMIUM=os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium"))
р = subprocess.run(["node", os.path.join(корінь, "аудит", "проби", "рв6_стенд.js"), "http://127.0.0.1:8765",
                    os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), "3"],
                   env=env, capture_output=True, text=True, timeout=900)
ряди = [л.split(" · ")[2:] for л in р.stdout.splitlines() if л.startswith("PLYTKA · всі · ")]
print("стенд-заглушка rc=%d · рядів %d" % (р.returncode, len(ряди)))
print("%-14s %-6s %-22s %-6s %-16s %s" % ("нагода", "плитка", "ошатність", "година", "звідки година", "збій"))
for ключ, є, ош, г, зв, зб in ряди:
    print("%-14s %-6s %-22s %-6s %-16s %s" % (ключ, є, ош, г, зв, зб[:60]))
print("з ошатністю: %d з %d плиток · година не з форми: %d" % (
    sum(1 for р_ in ряди if р_[1] == "true" and р_[2] != "null"), sum(1 for р_ in ряди if р_[1] == "true"),
    sum(1 for р_ in ряди if р_[1] == "true" and р_[4] not in ("—", ПН.ТИПОВЕ_ПОЛЕ_ФОРМИ))))
