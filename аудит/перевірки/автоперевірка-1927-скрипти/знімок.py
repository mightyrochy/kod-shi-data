"""Знімок каталогу дерева: FK.прочитати_каталог(feed.каталог_на_диску(), 0) у JSON."""
import json, os, sys, time
дерево, вихід = sys.argv[1], os.path.abspath(sys.argv[2])
дж = os.path.abspath(os.path.join(дерево, "джерела"))
os.chdir(дж); sys.path.insert(0, дж)
import feed, фід_каталог as FK
t = time.time()
р = FK.прочитати_каталог(feed.каталог_на_диску(), 0)
with open(вихід, "w", encoding="utf-8") as f:
    json.dump(dict(каталог=р["каталог"]), f, ensure_ascii=False, default=lambda o: list(o) if isinstance(o, (set, frozenset, tuple)) else str(o))
print("записів", len(р["каталог"]), "с", round(time.time() - t, 1))
