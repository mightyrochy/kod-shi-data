# -*- coding: utf-8 -*-
"""Самотест проби `текст_жінці_записи.py` (11292): синтетичний файл, у якому проба мусить побачити кожен вид обходу —
шаблон з `${}`, «виклик точки + сире», `append(рядок)`, `alert`, `.value` поза переліком, `.text`, вбудований скрипт `показ.html` —
і не бачити сталих записів. Запуск: python3 проби/текст_жінці_записи_самотест.py (код виходу 1 — проба сліпа до чогось)."""
import os, subprocess, sys, tempfile
ТУТ = os.path.dirname(os.path.abspath(__file__))
ОБХОДИ = [
    "е.textContent = `Не вдалось: ${причина}`;",
    "е.textContent = текстЖінціП(е, 'Готово') + сире;",
    "е.append('Помилка: ' + String(е));",
    "alert(текстВинятку);",
    "поле.value = відповідьМоделі;",
    "опція.text = назваСхеми;",
    "е.innerHTML = '<b>' + дані.назва + '</b>';",
]
СТАЛІ = [
    "е.textContent = 'Готово';",
    "текстЖінціП(е, 'Готово ' + дані.назва);",
    "е.append(ел('span', null, 'ok'));",
]
з_ходом = lambda рядки, html=False: "\n".join(рядки)
with tempfile.TemporaryDirectory() as д:
    os.makedirs(os.path.join(д, "показ"))
    open(os.path.join(д, "показ", "а.js"), "w", encoding="utf8").write(з_ходом(СТАЛІ))
    пусто = subprocess.run([sys.executable, os.path.join(ТУТ, "текст_жінці_записи.py"), д], capture_output=True, text=True).stdout.splitlines()[0]
    open(os.path.join(д, "показ", "а.js"), "w", encoding="utf8").write(з_ходом(СТАЛІ + ОБХОДИ[:6]))
    open(os.path.join(д, "показ.html"), "w", encoding="utf8").write("<script>\n" + ОБХОДИ[6] + "\n</script>")
    повно = subprocess.run([sys.executable, os.path.join(ТУТ, "текст_жінці_записи.py"), д], capture_output=True, text=True).stdout.splitlines()[0]
число = lambda р: int(р.split(":")[1].split("·")[0])
ок = число(пусто) == 0 and число(повно) == len(ОБХОДИ)
print("сталі: %s · обходи: %s (мусить бути %d) → %s" % (число(пусто), число(повно), len(ОБХОДИ), "ок" if ок else "ПРОБА СЛІПА"))
sys.exit(0 if ок else 1)
