"""ПАСПОРТ-36 (рядок 4622): перші ходи сцен «йога зранку, потім кава з подругою» і «Новорічна вечірка в ресторані,
надворі мороз» ЖИВІ-20…24 — записані відповіді мовної моделі тим кодом, що в теці аргументу (типово `.`):
`прийняти_розмову` → `паспорт_з_шару`. Друкує, що дала модель (occasion, place, place_words, movement) і що
стало в паспорт (нагода, місце, рух) з `не_взято_кодом` про місце; наприкінці — чи промпт ходу каже про спорт частини дня.
Кращим: у дні зі спортом і кафе — місце кафе й рух sport, хоч модель і поклала кафе підписом у `place_words`;
новорічна — місце не null там, де модель його дала.
Запуск: cd джерела && python3 проби/частини_дня_4622.py [тека джерел іншої збірки]"""
import json, subprocess, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for ж in ("20", "21", "22", "23", "24"):
    г = "origin/claude/zhyvi-" + ж
    git("fetch", "-q", "origin", "claude/zhyvi-" + ж)
    for ф in git("ls-tree", "-r", "--full-tree", "--name-only", г, "аудит/живі_%s/А" % ж).splitlines():
        if not ф.endswith("_01_мовний_шар_хід_розмови.txt") or not ("спорт_ком" in ф or "новорічна" in ф): continue
        с = git("show", "%s:%s" % (г, ф)); вх = json.loads(с.split("\n", 1)[1].split("\n── ВІДПОВІДЬ")[0])
        р = М.прийняти_розмову(с.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1])
        if р.get("причина"): print("Ж%s %s · без відповіді" % (ж, ф.split("/")[3][:2])); continue
        у = json.loads(с.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1].strip().strip("`").removeprefix("json"))["update"]
        ш = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=[вх["her_new_message"]], частини=р["частини"])
        п = ш["паспорт"]
        print("Ж%s №%s · модель: %s · паспорт: %s · %s" % (ж, ф.split("/")[3][:2],
              " ".join("%s=%s" % (к, (у[к] or {}).get("value") if isinstance(у.get(к), dict) else у.get(к))
                       for к in ("occasion", "place", "place_words", "movement") if к in у),
              " ".join("%s=%s" % (к, п.get(к)) for к in ("нагода", "місце", "рух", "подія")),
              [н[:60] for н in п.get("не_взято_кодом") or [] if "place" in н] or "—"))
п = json.loads(М.промпт_розмови({"розмова": {"нове": "йога зранку, потім кава з подругою", "історія": []}}))
print("промпт: намір обраної частини дня, незалежно від руху:",
      next(р for р in п["task"]["codes"] if р.startswith("- occasion_part")))
