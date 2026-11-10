"""Порівняння двох знімків `знімок.py` (ДО — база, ПІСЛЯ — голова) з причиною кожного переходу.

    python3 -W ignore аудит/перевірка/річ_колір_межі_крок24а/порівняти.py <до.json.gz> <після.json.gz>

Причини правок кроку: `_тепло` — полюси осі тепла `колір_тон` (h ≈ 98.3 / 253.9) замість h 90 / 270 CIELAB;
`певність_тону` — нижній край темного бурого L* − 3 через 0° (`в_дузі_пів`); `_буре` — належність дуги вікна
`дуга_в_дузі`; `bases.відхил_тону_ΔE` — поворот до межі боків h 25 / 157 замість h 0 / 180."""
import collections, gzip, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import колір_тон as Т, colorspace as КП  # noqa: E402

до, після = (json.load(gzip.open(ф, "rt")) for ф in sys.argv[1:3])
полюси = [Т.з_кола_художника(п) for п in Т.РЕЄСТР["полюси_температури"]["val"]]
print("полюси осі тепла, h CIELAB:", полюси, "· стара вісь b*: 90.0, 270.0")

зм = [к for к in до["записи"] if до["записи"][к] != після["записи"][к]]
print("записи: акцент/певність тону змінились у %d з %d" % (len(зм), len(до["записи"])), зм[:10])
for к in зм[:10]:
    print("   ", к, до["записи"][к], "→", після["записи"][к])

класи = collections.Counter(); приклади = collections.defaultdict(list)
wc = [0, 0]; wc_при = collections.defaultdict(list)
for к, (вд, сд, сбд) in до["пари"].items():
    вп, сп, сбп = після["пари"][к]
    for кл in вд:
        if вд[кл] != вп[кл]:
            класи[(кл, вд[кл], вп[кл])] += 1
            if len(приклади[кл]) < 4:
                приклади[кл].append(к)
    for і, (а, б) in enumerate(((сд, сп), (сбд, сбп))):
        if а != б:
            wc[і] += 1
            if len(wc_при[і]) < 12:
                wc_при[і].append("%s %s → %s" % (к, а, б))
print("пар %d; вердикт `колір_річ.відношення` змінився: %d" % (len(до["пари"]), sum(класи.values())), dict(класи))
for кл, пп in приклади.items():
    print("   ", кл, пп)
print("сила warm_cool змінилась: з певністю %d, без певності %d" % tuple(wc))
for і in (0, 1):
    for р in wc_при[і]:
        print("   ", ("з певністю", "без певності")[і], р)
# причина кожної зміни warm_cool: запис пари, дуга якого містить старий полюс (h 90 / 270) без нового чи навпаки
import колір_річ as КР, verify as V  # noqa: E402
from колір_тон import in_arc  # noqa: E402
тч = {"т:%s" % р[0]: {"lab": [float(x) for x in р[1]]} for р in json.load(gzip.open(
    Path(__file__).resolve().parents[1] / "річ_колір_межі_тон_20261105/каталог_точки.json.gz", "rt")) if р[1] is not None}
тч.update({"с:%s" % к: {"колір_не_вимір": {"вікно": list(в)}} for к, в in V.ЛЕКСИКОН.items()})
дуги = {к: КР.запис_кольору(x)["дуга"] for к, x in тч.items()}
def причина(ім):
    д = дуги[ім]
    if д is None:
        return None
    с = tuple(in_arc(x, д) for x in (90.0, 270.0)); н = tuple(in_arc(x, д) for x in полюси)
    return None if с == н else "%s: дуга %s, старий полюс %s, новий %s" % (ім, tuple(round(x, 1) for x in д), с, н)
пр = collections.Counter(); без_причини = 0
for к, (_, сд, сбд) in до["пари"].items():
    _, сп, сбп = після["пари"][к]
    if сд != сп or сбд != сбп:
        пп = [причина(ім) for ім in к.split("|")]
        пп = [x for x in пп if x]
        без_причини += not пп
        for x in пп:
            пр[x] += 1
print("причини зміни warm_cool (запис — у скількох змінених парах); пар без причини: %d" % без_причини)
for x, n in пр.most_common():
    print("   %5d  %s" % (n, x))

зв = collections.Counter(); зв_при = collections.defaultdict(list)
for к, (д1, д2) in до["відхил"].items():
    п1, п2 = після["відхил"][к]
    for поз, а, б in ((1, д1, п1), (-1, д2, п2)):
        if а != б:
            т = "0 → >0" if а == 0 else ">0 → 0" if б == 0 else "більше" if б > а else "менше"
            зв[(поз, т)] += 1
            if len(зв_при[(поз, т)]) < 3:
                зв_при[(поз, т)].append("%s %.2f → %.2f" % (к, а, б))
print("bases.відхил_тону_ΔE змінився (поз, напрям):", dict(зв))
смуги = collections.Counter()
for к, (д1, д2) in до["відхил"].items():
    п1, п2 = після["відхил"][к]
    for поз, а, б in ((1, д1, п1), (-1, д2, п2)):
        if а != б:
            h = КП.lch(тч[к]["lab"])[2]
            смуги[(поз, int(h // 30) * 30, "більше" if б > а else "менше")] += 1
print("   за смугами h CIELAB по 30° (поз, смуга, напрям):", sorted(смуги.items()))
for к, пп in зв_при.items():
    print("   ", к, пп)
жз = {ж: (до["жінки"][ж] != після["жінки"][ж]) for ж in до["жінки"]}
print("жінки з різницею палітр:", [ж for ж, з in жз.items() if з])


def шляхи(а, б, п=""):
    if type(а) is not type(б):
        yield п, а, б
    elif isinstance(а, dict):
        for к in sorted(set(а) | set(б)):
            yield from шляхи(а.get(к), б.get(к), п + "/" + к)
    elif isinstance(а, list) and len(а) == len(б):
        for і, (x, y) in enumerate(zip(а, б)):
            yield from шляхи(x, y, п + "[%d]" % і)
    elif а != б:
        yield п, а, б


for ж, з in жз.items():
    if з:
        дд = list(шляхи(до["жінки"][ж], після["жінки"][ж]))
        print("   %s: %d полів" % (ж, len(дд)), [д[0] for д in дд[:6]])
