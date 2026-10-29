"""Рядок 6570: «ви» і код словами в бульбашці ходу розмови (`says`) — на знімках живого прогону `ng4_rozmova_*.txt`
(поле «стилістка» — те, що жінка прочитала). Без теки — ДО, записи ЖИВІ-1016-1 (`claude/zhyvi-1016-1`); з текою —
ПІСЛЯ, тека живого прогону. Наостанок — чи стоять форми «ви» в правилі форми цього `мовний_шар` (антиприклад —
теж приклад, рядок 6195). Слова тут читає ПРОБА (мірило очима), не код.
Запуск: cd джерела && python3 проби/мова_ви_6570.py [<тека прогону>]"""
import json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, "."); import мовний_шар as М
from проби.мова_ти_5983 import ФОРМИ, НЕ_ФОРМИ
Г, Т = "origin/claude/zhyvi-1016-1", "аудит/живі_1016_1"
КОД_СЛОВАМИ = re.compile(r"(?i)[a-z]{3,}|контекст\w* оптимальн|оптимальн\w* контекст|конвенційн|стейтмент|комфорт перш")
def знімки():
    if len(sys.argv) > 1:
        return [(ф.relative_to(sys.argv[1]).parts[0], ф.read_text(encoding="utf-8"))
                for ф in sorted(Path(sys.argv[1]).rglob("ng4_rozmova_*.txt"))]
    ф = subprocess.run(["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", Г, "../" + Т],
                       capture_output=True, text=True).stdout.split()
    return [(п.split("/")[3], subprocess.run(["git", "show", "%s:%s" % (Г, п)], capture_output=True, text=True).stdout)
            for п in ф if re.search(r"знімки/ng4_rozmova_.*\.txt$", п)]
бульбашок = ви = код = 0
for сцена, т in знімки():
    б = json.JSONDecoder().raw_decode(т.lstrip())[0].get("стилістка") or ""
    ф = [м.group(1) for м in ФОРМИ.finditer(б) if м.group(1).lower() not in НЕ_ФОРМИ]
    к = КОД_СЛОВАМИ.findall(б)
    бульбашок, ви, код = бульбашок + 1, ви + bool(ф), код + bool(к)
    if ф or к:
        print("  %s: «ви» %s · код %s · %s" % (сцена, ф, к, б[:110]))
print("бульбашок %d · з «ви» %d · з кодом словами %d" % (бульбашок, ви, код))
print("форм «ви» у правилі форми:", [м.group(1) for м in ФОРМИ.finditer(М._ПРАВИЛО_ФОРМИ)
                                     if м.group(1).lower() not in НЕ_ФОРМИ])
