import importlib.util, sys, os, json, collections
def завант(ш, ім):
    сп = importlib.util.spec_from_file_location(ім, ш); м = importlib.util.module_from_spec(сп); сп.loader.exec_module(м); return м
корінь = sys.argv[1]
після = завант(корінь + "/zhnyvarka/жниварка.py", "після"); до = завант(sys.argv[2] if len(sys.argv) > 2 else "/tmp/пс2/ж_до.py", "до")
до.РЕЦЕПТИ_TSV = після.РЕЦЕПТИ_TSV
ПОЛЯ = ("опис", "характеристики_сирі", "характеристики", "свотчі", "розміри", "ціна", "фото", "є_товар", "таблиця_мірок", "available")
коди = dict(l.split()[:2] for l in open("/tmp/пс2/коди.txt"))
рез = []
for l in open("/tmp/пс2/список.txt"):
    n, h, u = l.split()
    if коди.get(n) != "200": continue
    т = open("/tmp/пс2/сторінки/%s.html" % n, encoding="utf8", errors="replace").read()
    try:
        a = до.факти_з_картки(т, u, до.рецепт_селекторів(h)); p = після.факти_з_картки(т, u, після.рецепт_селекторів(h))
    except Exception as e:
        print("ПОМИЛКА", n, h, e); continue
    зм = {к: (a.get(к), p.get(к)) for к in ПОЛЯ if json.dumps(a.get(к), sort_keys=True, default=str) != json.dumps(p.get(к), sort_keys=True, default=str)}
    рез.append(dict(n=n, h=h, u=u, межа=p.get("межа_блоку"), зм=зм))
json.dump(рез, open("/tmp/пс2/рез.json", "w"), ensure_ascii=False, default=str)
c = collections.Counter(р["межа"] for р in рез); print("сторінок", len(рез), "межа:", dict(c))
пк = collections.Counter(к for р in рез for к in р["зм"]); print("полів змінено ДО→ПІСЛЯ:", dict(пк))
втрачено = collections.Counter(к for р in рез for к, (a, b) in р["зм"].items() if a and not b); print("було значення → стало порожньо:", dict(втрачено))
print("є_товар True→False:", sum(1 for р in рез if р["зм"].get("є_товар", (0, 0))[0] is True and not р["зм"]["є_товар"][1]))
крамниці = collections.defaultdict(set)
for р in рез: крамниці[р["межа"]].add(р["h"])
for к, v in крамниці.items(): print(к, len(v), sorted(v) if len(v) < 15 else "")
