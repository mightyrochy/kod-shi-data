"""Порівняння двох знімків `тепло.py` (ДО — база, ПІСЛЯ — голова) з причиною кожного переходу.

    python3 аудит/перевірка/річ_колір_межі_крок23/порівняти.py <до.json.gz> <після.json.gz>

Перехід знака тепла — за смугами тону CIELAB і першою сім'єю `колір_тон.сім_я_кольору` голови; сила warm_cool пари —
скільки змінилось і на скільки; підтон точки як риси — матриця переходів; жінки — шляхи JSON `палітри`, що змінились."""
import collections, gzip, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import колір_тон as Т  # noqa: E402
from колір_простір_перетворення import lch, hex_з_lab  # noqa: E402

до, після = (json.load(gzip.open(ф, "rt")) for ф in sys.argv[1:3])
точки = {р[0]: р[1] for р in json.load(gzip.open(Path(__file__).resolve().parents[1] / "річ_колір_межі_тон_20261105/каталог_точки.json.gz", "rt")) if р[1] is not None}
знак = lambda т: "тепла" if т >= 0 else "холодна"
перехід, смуги, сім_ї, приклади = collections.Counter(), collections.Counter(), collections.Counter(), collections.defaultdict(list)
підтон, зсув = collections.Counter(), []
for (і, тд, пд), (_, тп, пп) in zip(до["точки"], після["точки"]):
    зсув.append(abs(тп - тд))
    підтон[(пд, пп)] += 1
    if знак(тд) != знак(тп):
        lab = точки[і]; _, C, h = lch(lab)
        к = (знак(тд), знак(тп)); перехід[к] += 1
        смуги[(к, int(h // 5) * 5)] += 1
        сім_ї[(к, Т.сім_я_кольору(lab)[0])] += 1
        if len(приклади[к]) < 4:
            приклади[к].append("%s %s h %.1f C %.1f" % (і, hex_з_lab(lab), h, C))
print("точок", len(до["точки"]), "· знак тепла змінився", sum(перехід.values()), dict(перехід))
print("|Δ тепла|: медіана %.3f, макс %.3f" % (sorted(зсув)[len(зсув) // 2], max(зсув)))
for к in перехід:
    print(" ", к, "смуги h:", sorted((с, n) for (кк, с), n in смуги.items() if кк == к))
    print(" ", к, "сім'ї:", sorted(((с, n) for (кк, с), n in сім_ї.items() if кк == к), key=lambda x: -x[1]))
    print(" ", к, "приклади:", приклади[к])
зм = [(а, б) for а, б in zip(до["пари"], після["пари"]) if а != б]
print("пари warm_cool: змінилось %d з %d; |Δ max| медіана %.3f, макс %.3f" % (
    len(зм), len(до["пари"]), sorted(abs(б[1] - а[1]) for а, б in зм)[len(зм) // 2] if зм else 0,
    max((abs(б[1] - а[1]) for а, б in зм), default=0)))
print("підтон точки як риси (ДО → ПІСЛЯ):")
for (а, б), n in sorted(підтон.items(), key=lambda x: -x[1]):
    print("   %s → %s: %d" % (а, б, n))
print("версії сімей (тепло середини ДО → ПІСЛЯ; порядок тепла > холодна):")
for ім in до["версії"]:
    а, б = до["версії"][ім], після["версії"][ім]
    п = lambda в: None if None in в.values() else в["тепла"] > в["холодна"]
    print("   %s: %s → %s; порядок %s → %s" % (ім, а, б, п(а), п(б)))
print("дуги нейтралей:", до["нейтралі"], "→", після["нейтралі"])


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


for ж in до["жінки"]:
    р = list(шляхи(до["жінки"][ж], після["жінки"][ж]))
    print("%s: змінено полів %d" % (ж, len(р)))
    for п, а, б in р[:6]:
        print("     %s: %s → %s" % (п, json.dumps(а, ensure_ascii=False)[:90], json.dumps(б, ensure_ascii=False)[:90]))
