#!/usr/bin/env python3
"""Стенд хука `.claude/хуки/фонові_завдання.py` (наряд хук-фонові-завдання): реальні виклики → рішення хука.

Запуск: python3 аудит/проби/хук_фонові_завдання.py [шлях_до_хука]   (без аргументу — хук з робочого дерева; шлях, якого
нема, — стан `main` до хука: кожен виклик іде як є).

Випадки — `хук_фонові_завдання_випадки.json`: 55 фонових `Bash` з транскриптів 24 сесій виконавців В.2 (22–29.10,
хвости `list_events`): 42 з `run_in_background`, 13 переведені у фон самим інструментом після `timeout`. Шлях scratchpad
замінено на `$SP`. Мірило: фоновий чекач (`sleep`, цикл до CI) — відмова; фонова робота — передній план (`timeout`
600000), і жодна з виміряно довгих не довша за 600 с + 30 хв фону після автопереходу; не фон — як є; зіпсований вхід —
як є з попередженням.
"""
import json
import os
import subprocess
import sys
from collections import Counter

ТУТ = os.path.dirname(os.path.abspath(__file__))
ХУК = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ТУТ, "..", "..", ".claude", "хуки", "фонові_завдання.py")
ФОН_ПІСЛЯ_АВТОПЕРЕХОДУ_С = 1800  # «If it is still running after 30m in the background, it will be stopped» (вимір 29.10)


def запуск(вхід):
    if not os.path.exists(ХУК):
        return "як є", ""
    р = subprocess.run([sys.executable, ХУК], input=вхід if isinstance(вхід, str) else json.dumps(вхід),
                       capture_output=True, text=True)
    if '"deny"' in р.stdout:
        return "відмова", р.stderr
    if "updatedInput" in р.stdout:
        новий = json.loads(р.stdout)["hookSpecificOutput"]["updatedInput"]
        return ("передній" if новий.get("run_in_background") is False and новий.get("timeout") == 600000
                else "інше: " + json.dumps(новий)[:80]), р.stderr
    return "як є", р.stderr


def очікуване(в):
    if not в["run_in_background"]:
        return "як є"
    return "відмова" if в["вид"] == "чекач" else "передній"


def main():
    with open(os.path.join(ТУТ, "хук_фонові_завдання_випадки.json"), encoding="utf-8") as ф:
        випадки = json.load(ф)
    таблиця, вади = Counter(), []
    for в in випадки:
        вхід = {"tool_name": "Bash", "tool_input": {"command": в["команда"], "run_in_background": в["run_in_background"]}}
        if в["timeout"]:
            вхід["tool_input"]["timeout"] = в["timeout"]
        рішення, _ = запуск(вхід)
        т = в["тривалість_с"]
        довжина = "?" if т is None else "< 10 хв" if т < 600 else "≥ 10 хв"
        таблиця[("фон" if в["run_in_background"] else "автофон", в["вид"], довжина, рішення)] += 1
        if рішення != очікуване(в):
            вади.append(f"{в['сесія']} {в['час']}: {рішення}, треба {очікуване(в)} — {в['команда'][:80]!r}")
        if рішення == "передній" and т is not None and т > 600 + ФОН_ПІСЛЯ_АВТОПЕРЕХОДУ_С:
            вади.append(f"{в['сесія']} {в['час']}: {т} с — зупинилось би після автопереходу")
    синтетичні = [
        ("зіпсований вхід", "{не json", "як є"),
        ("Agent у фоні", {"tool_name": "Agent", "tool_input": {"prompt": "x", "run_in_background": True}}, "як є"),
        ("Bash без поля", {"tool_name": "Bash", "tool_input": {"command": "ls"}}, "як є"),
        ("фон з timeout 7200000", {"tool_name": "Bash", "tool_input": {"command": "python3 x.py",
                                                                        "run_in_background": True, "timeout": 7200000}},
         "передній"),
        ("чекач while", {"tool_name": "Bash", "tool_input": {"command": "while ! test -f a; do sleep 5; done",
                                                             "run_in_background": True}}, "відмова"),
        ("без tool_input", {"tool_name": "Bash"}, "як є"),
    ]
    for назва, вхід, треба in синтетичні:
        рішення, stderr = запуск(вхід)
        таблиця[("синтетичний", назва, "", рішення)] += 1
        if рішення != треба:
            вади.append(f"{назва}: {рішення}, треба {треба}")
    print("| виклик | вид | тривалість | рішення хука | випадків |\n|---|---|---|---|---|")
    for к in sorted(таблиця):
        print(f"| {' | '.join(к)} | {таблиця[к]} |")
    пропущено = sum(1 for в in випадки if в["run_in_background"] and запуск(
        {"tool_name": "Bash", "tool_input": {"command": в["команда"], "run_in_background": True}})[0] == "як є")
    print(f"\nфонових викликів пропущено як є: {пропущено} з {sum(в['run_in_background'] for в in випадки)}; "
          f"розбіжностей з мірилом: {len(вади)}")
    for в in вади:
        print("  " + в)
    sys.exit(1 if вади else 0)


if __name__ == "__main__":
    main()
