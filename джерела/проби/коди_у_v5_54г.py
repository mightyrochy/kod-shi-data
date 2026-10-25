"""5.4-Г: чи виражає форма V5 (`каталог_розбір.взірці()["codes"]`) коди частини 1 — 663 речі з
`каталог_розбір_коди.json.gz`, без моделі — і що з них робить код: пункт на кожен код, що не unknown (модель
not_applicable пише лише на типі), цитата — заглушка «ц» (у мірки — з її числом), що стоїть у тексті; `з_відповіді` ставить слот і
not_applicable сам. Друкує: скільки речей у взірці, пунктів на річ, і де поле після коду розійшлось з частиною 1.
python3 проби/коди_у_v5_54г.py"""
import gzip, json, re, collections, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір as Р
к = json.load(gzip.open(Path(__file__).resolve().parents[1] / "каталог_розбір_коди.json.gz", "rt"))
вз, НА = re.compile(Р.взірці()[Р.КОДИ]), Р.НЕ_СТОСУЄТЬСЯ
def зн(річ, шлях):
    """Коди поля частини 1 списком рядків (мірка — «95 cm»)."""
    кр = Р._кроки(шлях); x = річ.get(кр[0][0])
    if кр[0][1]:
        x = [ч.get(кр[1][0]) if isinstance(ч, dict) else ч for ч in x or []] if len(кр) > 1 else x or []
    else:
        x = [(x or {}).get(кр[1][0], "unknown") if len(кр) > 1 else x]
    return ["%g %s" % (в["value"], в["unit"]) if isinstance(в, dict) else str(в) for в in x]
гаразд, пунктів, розійшлось = 0, [], collections.Counter()
for і, р in к.items():
    тип = зн(р, Р.ТИП)[0]
    пп = ["%s=%s=ц" % (Р.ТИП, тип) if тип != "unknown" else "%s=unknown" % Р.ТИП]
    пп += ["%s=%s=ц%s" % (Р._ключ_коду(ш), в, в.split()[0] if " " in в else "") for ш, _, _ in Р._листки()
           if ш != Р.ТИП for в in зн(р, ш) if в not in ("unknown", НА)]     # мірка: число — у цитаті
    рядок = ";".join(пп); пунктів.append(len(пп))
    гаразд += bool(вз.fullmatch(рядок))
    після, _ = Р.з_відповіді(json.dumps({Р.КОДИ: рядок, Р.ОСОБЛИВОСТІ: ""}, ensure_ascii=False), {"name": " ".join(п.split("=")[-1] for п in пп)})
    for ш, _, _ in Р.ПОЛЯ:
        if ш not in Р.ВИВЕДЕНІ and зн(р, ш) != зн(після, ш):
            розійшлось[(ш, ",".join(зн(р, ш)), ",".join(зн(після, ш)))] += 1
пунктів.sort()
print("коди 663 у взірці codes V5: %d з %d; пунктів на річ p50 %d, p99 %d, найбільше %d (стеля %d)"
      % (гаразд, len(к), пунктів[len(пунктів) // 2], пунктів[len(пунктів) * 99 // 100], пунктів[-1], Р.СТЕЛЯ_ПУНКТІВ))
рід = lambda б, с: "unknown→NA (таблиця)" if (б, с) == ("unknown", НА) else "NA→unknown" if (б, с) == (НА, "unknown") else "інше"
за_родом = collections.Counter()
for (ш, б, с), н in розійшлось.items(): за_родом[рід(б, с)] += н
print("полів, де код після V5 розійшовся з частиною 1: %s; NA→unknown і інше: %s" % (dict(за_родом),
      [(к, н) for к, н in розійшлось.most_common() if рід(*к[1:]) != "unknown→NA (таблиця)"][:8]))
