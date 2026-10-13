"""Рядок 4280: replay записаної відповіді стилістки Ж19 (`seed3_08`, рука 3 №11) через `мовний_шар.розмітити` тим кодом, що
в теці аргументу (типово `.`) — те, що йде в перекладача (`seed3_16`). Друкує кожен рядок із hex: що стало на місці hex.
«Без назви» = у рядку нема ні `[colour: …]`, ні її слова кольору (`_слова_кольору`). Запуск: cd джерела && python3 проби/реплей_4280.py [тека]"""
import re, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import мовний_шар as М
Г, Д = "origin/claude/zhyvi-19", "аудит/живі_19/А/11_ж2_новорічна_мороз/VIDPOVIDI/"
т = subprocess.run(["git", "-c", "core.quotepath=false", "show", Г + ":" + Д + "seed3_08_проза_рука_3_4.txt"],
                   capture_output=True, text=True).stdout.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1].split("\n── ПРОМПТ")[0]
вхід = М.розмітити({"1": т.strip()})[0]["текст"]
без = 0
КОД = set(М._СИНОНІМИ_КОЛЬОРУ) | {к.split("_")[-1] for к in М._ВМ.ТАБЛИЦЯ["color_name"]}   # її слова кольору без «soft», «light»
for р, ц in zip(т.strip().split("\n"), вхід.split("\n")):
    є_hex, слова = re.search(r"#[0-9a-fA-F]{6}", р), {w.lower() for w in re.findall(r"[A-Za-z]+", ц)} & КОД
    if not є_hex:
        continue
    назва = "[colour:" in ц or bool(слова)
    без += bool(є_hex) and not назва
    print("%s | %s" % ("назва є" if назва else "БЕЗ НАЗВИ", ц[:110]))
print("рядків з hex без назви кольору: %d" % без)
