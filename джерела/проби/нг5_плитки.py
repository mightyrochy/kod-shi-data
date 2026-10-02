# -*- coding: utf-8 -*-
"""НГ-5 (рядки 752–754): набір плиток нагоди — довідник, аркуш сценарію й список «Оціни мій образ»; і для кожної
плитки БЕЗ розмови — що паспорт дістає з ходу плиток (ошатність — число моделі, година й звідки вона: `form` —
типові 11:00 форми, інше — частина дня від ходу). Без аргументів — лише довідник; з `<тека зі зібраним index.html>
<тека Pyodide>` — ще й стенд-заглушка `PLYTKA=всі` (`аудит/проби/рв6_стенд.js`, сід 3). Запуск із `джерела`;
ганяти на двох SHA й порівняти."""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import паспорт_нагоди as ПН
н = ПН.довідник()["нагоди"]
print("довідник: нагод %d · плиткою %d — %s" % (len(н), sum(р["плитка"] for р in н),
      " | ".join(р["підпис"] for р in н if р["плитка"])))
if len(sys.argv) < 3:
    sys.exit(0)
корінь = os.path.dirname(sys.path[0])
env = dict(os.environ, PLYTKA="всі", NODE_PATH=os.path.join(sys.path[0], "node_modules"),
           CHROMIUM=os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium"))
р = subprocess.run(["node", os.path.join(корінь, "аудит", "проби", "рв6_стенд.js"), "http://127.0.0.1:8765",
                    os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), "3"],
                   env=env, capture_output=True, text=True, timeout=900)
for л in р.stdout.splitlines():
    if л.startswith(("PLYTKA · аркуш", "PLYTKA · оціни", "PLYTKA · підсвічено")):
        print(л[9:])
ряди = [л.split(" · ")[2:] for л in р.stdout.splitlines() if л.startswith("PLYTKA · плитка · ")]
print("стенд-заглушка rc=%d · плиток пройдено %d" % (р.returncode, len(ряди)))
print("%-10s %-10s %-6s %-14s %s" % ("плитка", "ошатність", "година", "звідки година", "збій"))
for ключ, ош, г, зв, зб in ряди:
    print("%-10s %-10s %-6s %-14s %s" % (ключ, ош, г, зв, зб[:60]))
print("з ошатністю: %d з %d · година від ходу (не з форми): %d" % (sum(1 for р_ in ряди if р_[1] != "null"),
      len(ряди), sum(1 for р_ in ряди if р_[3] not in ("—", ПН.ТИПОВЕ_ПОЛЕ_ФОРМИ))))
