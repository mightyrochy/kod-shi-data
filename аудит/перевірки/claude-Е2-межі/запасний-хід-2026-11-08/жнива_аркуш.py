# Проба: аркуш класів у жнива_кадри при збої моделі після повторів — прогін падає чи йде далі з причиною
import sys, os, hashlib, tempfile
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import жнива_кадри as Ж, жнива_запис as ЖЗ
from PIL import Image
def _збій(*а, **к): raise ValueError("не JSON (not_json): ''")
ЖЗ._запит = _збій
т = tempfile.mkdtemp(); записи = []
for і in range(3):
    ш = os.path.join(т, "%d.jpg" % і); Image.new("RGB", (64, 64), (і * 40, 80, 120)).save(ш)
    url = "https://x/%d.jpg" % і
    Ж._індекс[hashlib.md5(url.encode()).hexdigest()] = {"шлях": ш}
    записи.append({"url": url, "lab": [50, 0, 0]})
try:
    n = Ж.аркуш_речі({"id": "ж-1@x", "параметри": {"тип": "сукня"}}, записи, "модель")
    print("прогін іде далі: класів", n, "· з причиною", sum(1 for в in записи if в.get("клас_чому")), "з", len(записи))
except Exception as e:
    print("ЗУПИНКА прогону:", type(e).__name__, str(e)[:80]); sys.exit(1)
