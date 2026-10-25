"""5.4-Г: чи виражає форма V4 (`каталог_розбір.взірці()["codes"]`) усі коди частини 1 — 663 речі з
`каталог_розбір_коди.json.gz`, без моделі. python3 проби/коди_у_v4_54г.py"""
import gzip, json, re, collections, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір as Р
к = json.load(gzip.open(Path(__file__).resolve().parents[1] / "каталог_розбір_коди.json.gz", "rt"))
вз = re.compile(Р.взірці()[Р.КОДИ])
def зн(річ, шлях):
    кр = Р._кроки(шлях); x = річ.get(кр[0][0])
    if кр[0][1]:
        x = x or []
        x = [ч.get(кр[1][0], "unknown") if isinstance(ч, dict) else ч for ч in x] if len(кр) > 1 else x
        return ",".join(map(str, x))
    if len(кр) > 1: x = (x or {}).get(кр[1][0], "unknown")
    if isinstance(x, dict): x = "%g %s" % (x["value"], x["unit"])
    return str(x)
погані = collections.Counter(); гаразд = 0
for і, р in к.items():
    рядок = ";".join("%s=%s" % (Р._ключ_коду(ш), зн(р, ш)) for ш, _, _ in Р._листки())
    if вз.fullmatch(рядок): гаразд += 1; continue
    for ш, п, _ in Р._листки():
        if not re.fullmatch(Р._взірець_коду(ш, п), зн(р, ш)): погані[(ш, зн(р, ш))] += 1
print("коди 663 у взірці codes V4: %d з %d; поза ним: %s" % (гаразд, len(к), погані.most_common(8)))
