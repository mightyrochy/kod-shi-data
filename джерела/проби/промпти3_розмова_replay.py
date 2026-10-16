"""ПРОМПТИ-3 (рядки 6186–6188): replay усіх записаних ходів розмови ЖИВОЇ ПАЧКИ-15 (`claude/zhyvi-pachka-15`) тим самим
кодом читання (`прийняти_розмову`), без моделі. Правка міняє лише промпт, тож поля, які код бере з тієї самої відповіді,
мають лишитись ті самі: на `main` (ДО) і на гілці (ПІСЛЯ) друк однаковий, до останнього рядка-відбитка.
На хід: сцена, сід і номер виклику — поля внутрішньої мови (з formality, month, part_of_day, place, occasion, movement).
Запуск: cd джерела && python3 проби/промпти3_розмова_replay.py"""
import hashlib, json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
Г, Т = "origin/claude/zhyvi-pachka-15", "аудит/живі_пачка_15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", Г.split("/", 1)[1])
ходи = [ф for ф in git("ls-tree", "-r", "--name-only", Г, "../" + Т).split("\n") if "_мовний_шар_хід_розмови" in ф]
ПОЛЯ = ("formality", "month", "part_of_day", "place", "occasion", "movement")
відбиток, з_полем = hashlib.sha1(), {п: 0 for п in ПОЛЯ}
for ф in sorted(ходи):
    т = git("show", "%s:%s" % (Г, ф))
    р = М.прийняти_розмову(т.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]) if "── ВІДПОВІДЬ" in т else {}
    в = р.get("внутрішня") or {}
    рядок = json.dumps(в, ensure_ascii=False, sort_keys=True, default=str)
    відбиток.update(рядок.encode())
    for п in ПОЛЯ:
        з_полем[п] += п in в
    print(ф.split("/")[-3][:26], re.sub(r".*(seed\d+_\d+).*", r"\1", ф), "| ключі:", ",".join(sorted(в))[:150])
print("ходів %d · з полем: %s · відбиток полів %s" % (len(ходи), з_полем, відбиток.hexdigest()[:16]))
