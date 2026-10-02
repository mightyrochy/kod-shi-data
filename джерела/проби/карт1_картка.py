# -*- coding: utf-8 -*-
"""КАРТ-1: що картка сценарію пише в «Де» й «Ошатність» і яке число ошатності дала мовна модель (стенд-заглушка,
`аудит/проби/рв6_стенд.js`, сід 3). 4 сцени: денне весілля 11:00, корпоратив у ресторані 20:00 (розмова), театр плиткою
(до збору і після), офіс (розмова). Розбіжність = слово картки не те, що назвало б число моделі. Запуск з кореня:
python3 джерела/проби/карт1_картка.py <тека зі зібраним index.html> <тека Pyodide>; ганяти ДО і ПІСЛЯ й порівняти."""
import json, os, subprocess, sys
К = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(К, "джерела")); os.chdir(os.path.join(К, "джерела"))
import паспорт_нагоди as ПН
КОДИ = [к for к in ПН.довідник()["коди"] if к["плитка"]]
def слово(д):
    с = (d[0] + d[1]) / 2 if (d := д) else 0
    return min(КОДИ, key=lambda к: abs(sum(к["діапазон"]) / 2 - с))["підпис"]
СЦЕНИ = [("весілля вдень 11:00", dict(DO="rozmova", CHAT_TEXT="Йду гостею на весілля подруги, розпис об 11:00",
          PASPORT='{"нагода":"весілля_гість","місце":"весілля_денне","година":11,"ошатність":[6,8]}')),
         ("корпоратив у ресторані 20:00", dict(DO="rozmova", CHAT_TEXT="Корпоратив у ресторані в пʼятницю ввечері, буде все начальство",
          PASPORT='{"нагода":"робота","місце":"ресторан_високий","година":20,"ошатність":[6,8]}')),
         ("театр плиткою", dict(PLYTKA="театр")), ("офіс розмовою", dict(DO="rozmova"))]
for назва, змінні in СЦЕНИ:
    env = dict(os.environ, NODE_PATH=os.path.join(К, "джерела", "node_modules"), CHROMIUM=os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium"), **змінні)
    р = subprocess.run(["node", os.path.join(К, "аудит/проби/рв6_стенд.js"), "http://127.0.0.1:8765", os.path.abspath(sys.argv[1]),
                        os.path.abspath(sys.argv[2]), "3"], env=env, capture_output=True, text=True, timeout=900)
    print("== %s (rc=%d)" % (назва, р.returncode))
    for л in р.stdout.splitlines():
        if л.startswith("KARTKA · "):
            к = json.loads(л.split(": ", 1)[1]); чм = к["число_моделі"]
            print("  %-14s Де: %-34s Ошатність: %-36s число моделі: %s (слово %s) година моделі: %s%s" % (л[9:].split(":")[0], к["де"], к["ошатність_картки"], чм,
                  слово(чм) if чм else "—", к["година_моделі"], "  ← РОЗБІЖНІСТЬ" if чм and not к["дрес_код_моделі"] and слово(чм) not in (к["ошатність_картки"] or "") else ""))
