"""ДО/ПІСЛЯ сімей речей каталогу з виводів `каталог_сім_ї.py`; argv: до.json після.json."""
import json, sys, collections as co
Д, П = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
пер = co.Counter((Д[i]['с'], П[i]['с']) for i in Д if Д[i]['с'] != П[i]['с'])
print("змінилось:", sum(пер.values()), "з", len(Д))
for (а, б), n in пер.most_common(): print("  %-22s → %-12s %d" % (а, б, n))
print("ПІСЛЯ:", co.Counter(v['с'] for v in П.values() if not v['с'].startswith('нейтраль')).most_common())
print("нейтралі ДО/ПІСЛЯ:", sum(v['с'].startswith('нейтраль') for v in Д.values()), sum(v['с'].startswith('нейтраль') for v in П.values()))
for корінь in ("рожев", "пудр", "фукс", "малин", "корал", "персик", "бірюз", "м'ят", "олив", "лаванд", "бузк", "фіолет"):
    xs = [i for i in П if корінь in (П[i]['слово'] or '').lower() and not П[i]['с'].startswith('нейтраль')]
    if xs: print("%-8s n=%4d ДО %s | ПІСЛЯ %s" % (корінь, len(xs), dict(co.Counter(Д[i]['с'] for i in xs).most_common(3)), dict(co.Counter(П[i]['с'] for i in xs).most_common(4))))
