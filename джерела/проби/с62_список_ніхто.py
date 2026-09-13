# -*- coding: utf-8 -*-
"""Проба Н-02-03 (С-62) по списку «ніхто» з `аудит/ДОСЯЖНІСТЬ.md`: для кожного
імені зі списку — чи є виклик із продукту, тесту або приладу. Друкує факти.
Прогін: python3 проби/с62_список_ніхто.py"""
import ast, io, os, subprocess, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import status

# Список «ніхто» станом на прогін `досяжність.py` 13.09.2026 (база С-61).
СПИСОК = [("status_перевірки", "_теплова_функція_не_виводиться_з_фіду"),
          ("status_перевірки", "_верхнього_одягу_в_живих_фідах_нуль"),
          ("status_перевірки", "_коди_без_корпусу"),
          ("міст_http", "H.log_message"),
          ("міст_http", "H.do_POST")]

def згадки(ім):
    вих = subprocess.run(["grep", "-rn", "--include=*.py", "--include=*.js",
                          "--include=*.html", r"\b%s\b" % ім, "."],
                         capture_output=True, text=True).stdout
    return [р for р in вих.split("\n") if р and not р.startswith("./аудит/")]

print("список «ніхто» з ДОСЯЖНІСТЬ.md — що з ним зробила С-62:")
for мод, ім in СПИСОК:
    коротке = ім.split(".")[-1]
    є_файл = os.path.exists(мод + ".py")
    оголошена = False
    if є_файл:
        for в in ast.walk(ast.parse(io.open(мод + ".py", encoding="utf-8").read())):
            if isinstance(в, ast.FunctionDef) and в.name == коротке:
                оголошена = True
    рядки = згадки(коротке)
    print("  %-18s %-42s оголошена: %-5s згадок у дереві: %d"
          % (мод, ім, "так" if оголошена else "НЕМА", len(рядки)))
    for р in рядки[:3]:
        print("      ", р[:120])

print()
print("перевірки статусу після знесення (жодна не має лишитись зламаною):")
import status_перевірки as SP
р = SP.перевірити()
print("  живі %d · застарілі %d · без_перевірки %d · зламані %s"
      % (len(р["живі"]), len(р["застарілі"]), len(р["без_перевірки"]), р["зламані"] or "жодної"))

print()
print("«ніхто» у ЯДРІ (status.МОДУЛІ_ПРОДУКТУ) за цим списком:",
      [ім for мод, ім in СПИСОК if мод in status.МОДУЛІ_ПРОДУКТУ] or "жодного")
