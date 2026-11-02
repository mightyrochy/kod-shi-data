import sys, os, json, glob, urllib.request, io
sys.path.insert(0, r"C:\Users\Admin\claude-run\w\20261031-175935-807f71a6d4d1\repo\джерела")
import каталог_розбір_прогін as P
_u = urllib.request.urlopen
журнал = []
class Т:
    def __init__(s, r): s.r = r
    def read(s, *a):
        d = s.r.read(*a)
        try: журнал.append((json.loads(d).get("usage") or {}).get("prompt_tokens"))
        except Exception: журнал.append(None)
        return d
    def __enter__(s): s.r.__enter__(); return s
    def __exit__(s, *a): return s.r.__exit__(*a)
def uo(з, *a, **k):
    if isinstance(з, urllib.request.Request) and "chat/completions" in з.full_url:
        b = json.loads(з.data); b["max_tokens"] = 1
        з = urllib.request.Request(з.full_url, data=json.dumps(b, ensure_ascii=False).encode("utf-8"), headers=з.headers)
    return Т(_u(з, *a, **k))
urllib.request.urlopen = uo
Г = P.Годинник(паралельно=2) if hasattr(P, "Годинник") else None
рез = []
for f in sorted(glob.glob(sys.argv[1] + "/[0-9]*.txt")):
    t = open(f, encoding="utf-8").read().replace("\r\n", "\n")
    повід = t.split("── ЗАПИТ\n", 1)[1].partition("\n\n── ВІДПОВІДЬ\n")[0]
    n0 = len(журнал)
    try:
        P.модель(повід, sys.argv[2], None, True, Г)
    except Exception as e:
        pass
    рез.append((os.path.basename(f), журнал[n0:] ))
json.dump(рез, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
п = [x[1][-1] for x in рез if x[1] and x[1][-1]]
print(len(рез), len(п), "max", max(п), "sum", sum(п))
print(Г.зведення() if Г and hasattr(Г, "зведення") else "")
