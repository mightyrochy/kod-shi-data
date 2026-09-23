# Рядок 139: річ, чия «назва» — перше речення опису, діставала слот із реклами, і
# слінгбеки їхали в «пояс» (образ ніс дві пари взуття). ДО/ПІСЛЯ на повному каталозі.
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import feed, фід_слот as FS

СТОПА = ("стоп", "носок", "п'ят", "п’ят", "підошв", "устілк", "закритим мисом", "слінгбек",
         "сандал", "босоніж", "черевик", "туфл", "кросівк", "балетк", "лофер", "взутт")
ЦІЛІ = ("ж-10663@jecomestudio.com", "ж-10662@jecomestudio.com",
        "ж-08906@jecomestudio.com", "ж-08907@jecomestudio.com")
к = feed.читати_yml(feed.каталог_на_диску("каталог_повний.xml"))
к = к[0] if isinstance(к, tuple) else к
після = {o["id"]: feed.слот(o) for o in к}
FS._рід_переважує_оголошення = lambda *а: False           # поведінка до правки
до = {o["id"]: feed.слот(o) for o in к}

def стопа(o):
    т = "%s %s" % (o.get("назва", ""), (o.get("параметри") or {}).get("опис", ""))
    return any(x in т.lower() for x in СТОПА)

реч = [o for o in к if ((o.get("параметри") or {}).get("назва_джерело") or "") == "опис"]
print("назва = перше речення опису: %d речей, %d крамниць; лежали ДО: %s"
      % (len(реч), len({o["магазин"] for o in реч}),
         dict(collections.Counter(до[o["id"]] for o in реч).most_common())))
зм = {i: (до[i], після[i]) for i in до if до[i] != після[i]}
print("змінили слот: %d із %d" % (len(зм), len(до)))
for (a, b), n in collections.Counter(зм.values()).most_common():
    print("   %-14s -> %-14s %4d" % (a, b, n))
взут = sorted(i for i in зм if зм[i] == ("пояс", "взуття"))
print("«поясів», що були взуттям: %d — %s …" % (len(взут), ", ".join(взут[:3])))
print("пояс ДО %d -> ПІСЛЯ %d" % (sum(1 for с in до.values() if с == "пояс"),
                                  sum(1 for с in після.values() if с == "пояс")))
print("поясів зі словом про стопу: ДО %d -> ПІСЛЯ %d"
      % (sum(1 for o in к if до[o["id"]] == "пояс" and стопа(o)),
         sum(1 for o in к if після[o["id"]] == "пояс" and стопа(o))))
збої = (sum(1 for o in к if після[o["id"]] == "пояс" and стопа(o))
        + sum(1 for i in ЦІЛІ if після[i] != "взуття"))
print("ВПАЛО %d" % збої)
sys.exit(1 if збої else 0)
