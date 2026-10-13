"""ОПИС-1 (рядки 1416, 1426, 1428–1430): вимір опису на теках прогонів (картки.txt, вердикти, відповіді).
python3 проби/опис_1_вимір.py <тека_клітинки> … — друкує факт на клітинку і разом."""
import sys, re, json, gzip, tarfile, statistics as st
РЕГ = {"найдальш": r"найдальш", "діагональ": r"діагонал|навскіс|навскос|кросбоді",
       "назва_vs_фото": r"[Уу] назві[^.]{0,80}(але|а) на фото|(в|у) коді", "обрив_…": r"(\.\.\.|…)\s*$"}
def клітинка(т):
    к = open(т + "/картки.txt", encoding="utf8").read()
    картки = re.split(r"═══ картка \d+ з \d+ · рука (\d)", к)[1:]
    чому, ряд, сумка, як = [], {k: 0 for k in РЕГ}, 0, 0
    for рука, тіло in zip(картки[0::2], картки[1::2]):
        м = re.search(r"\nЧому цей образ\n(.*?)\n(Як це носити|Приміряти на себе)\n", тіло, re.S)
        if рука in "12" and м: чому.append(len(м.group(1)))
        for k, r in РЕГ.items():
            ряд[k] += sum(1 for л in тіло.split("\n") if re.search(r, л))
        н = re.search(r"\nЯк це носити\n(.*?)\nПриміряти на себе\n", тіло, re.S)
        if н:
            лін = [л for л in н.group(1).split("\n") if л.strip()]
            як += len(лін); сумка += sum(1 for л in лін if re.search(r"сумк|клатч|рюкзак", л, re.I))
    опис = без = 0
    with tarfile.open(т + "/відповіді.tar.gz") as тар:
        for ч in тар.getmembers():
            if "ОПИС" in ч.name and ч.isfile():
                п = тар.extractfile(ч).read().decode("utf8")
                м = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*?)\n\n── ВІДПОВІДЬ", п, re.S)
                if м: опис += 1; без += '"idea"' not in м.group(1)
    в = gzip.open(т + "/вердикти.txt.gz", "rt", encoding="utf8").read()
    знято = len(set(re.findall(r'слова_знято":"([^"]*)"', в))); заяви = len(set(re.findall(r'заяви_знято":"([^"]*)"', в)))
    поза = len(re.findall(r"description_named_not_in_outfit=", в)); урізано = len(re.findall(r"cut_after_retry=|cut: ", в))
    return dict(чому=чому, опис=опис, без_idea=без, знято=знято, заяви_знято=заяви, як=як, як_сумка=сумка,
                названо_поза=поза, урізано=урізано, **ряд)
усі = {}
for т in sys.argv[1:]:
    р = клітинка(т.rstrip("/")); усі[т] = р
    print(т.rstrip("/").split("/")[-1], json.dumps(р, ensure_ascii=False))
ч = [x for р in усі.values() for x in р["чому"]]
print("РАЗОМ: «Чому цей образ» р1–2 медіана %s (n=%d, макс %s);" % (st.median(ч) if ч else "—", len(ч), max(ч or [0])),
      ", ".join("%s %d" % (k, sum(р[k] for р in усі.values())) for k in list(РЕГ) + ["опис", "без_idea", "знято",
                "заяви_знято", "як", "як_сумка", "названо_поза", "урізано"]))
