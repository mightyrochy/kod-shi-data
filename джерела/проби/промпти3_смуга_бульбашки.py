"""Рядок 6189: replay 28 записаних ходів розмови ж15 (`claude/zhyvi-pachka-15`, `аудит/живі_пачка_15`) тим самим кодом,
без моделі: `прийняти_розмову` → бульбашка (`_текст_до_показу`). Лічба бульбашок зі смугою ошатності — «рівн»,
«формальн» чи «N–M» (лічба на виході, код продукту слів не читає, п.12) — і речень, знятих за formality в `about`
(`чому=about_scale`). Кращим: смуга 0. Запуск: cd джерела && python3 проби/промпти3_смуга_бульбашки.py"""
import re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
Г, Т = "origin/claude/zhyvi-pachka-15", "../аудит/живі_пачка_15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/zhyvi-pachka-15")
СМУГА = re.compile(r"рівн|формальн|\d\s*[–-]\s*\d", re.I)
ходів = смуга = знято = 0
for ф in sorted(ф for ф in git("ls-tree", "-r", "--name-only", Г, Т).split("\n") if "_хід_розмови" in ф):
    т = git("show", "%s:%s" % (Г, ф))
    р = М.прийняти_розмову(т.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1])
    ходів += 1
    з = [x for x in р["відкинуто"] if x.get("чому") == "about_scale"]
    знято += len(з)
    if СМУГА.search(р["текст"] or ""):
        смуга += 1
        print(ф.split("/")[-3][:22], ф.split("/")[-1][:8], "|", (р["текст"] or "")[:150])
print("ходів:", ходів, "| бульбашок зі смугою:", смуга, "| знято речень з formality в about:", знято)
