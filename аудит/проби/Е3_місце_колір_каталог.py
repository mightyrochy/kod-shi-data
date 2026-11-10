"""Весь каталог: місце без виміру й слова стилістки на контрольному профілі; --до SHA бере старі читачі."""
import os, sys, json, collections, subprocess, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
ДЖ = КОРІНЬ / "джерела"
sys.path.insert(0, str(ДЖ)); os.chdir(ДЖ)
тимчасова = tempfile.TemporaryDirectory()
if "--до" in sys.argv:
    sha = sys.argv[sys.argv.index("--до") + 1]
    for ім in ("колір_світлота", "колір_нейтралі", "палітра_запити", "аксесуари_структура", "повнота_образу", "річ_з_фото"):
        текст = subprocess.check_output(["git", "show", f"{sha}:джерела/{ім}.py"], encoding="utf-8")
        Path(тимчасова.name, ім + ".py").write_text(текст, encoding="utf-8")
    sys.path.insert(0, тимчасова.name)
import фід_каталог as ФК, feed as Ф, композитор_річ as Р, outfit as О
import колір_світлота as КС, колір_нейтралі as КН, аксесуари_структура as А
import colorspace as Ц, місце_речі as М
ліч = collections.Counter()
особа = dict(доступно=True, L_шкіри=75, value_gap=15)
F = Ц.features(Ц.hx("#deb295"), Ц.hx("#f1dbaa"), Ц.hx("#759087"))
кат = ФК.прочитати_каталог(Ф.каталог_на_диску(), 0)["каталог"]
for c in кат:
    ліч["каталог"] += 1
    if not c.get("слот"):
        ліч["без слота"] += 1; continue
    р = Р.у_річ(c, c["слот"], None); E = О.елементи([р])
    ліч["з елементом кольору"] += bool(E)
    for ім, з in (("K-CLR-02", КС.біля_обличчя(E, особа)),
                  ("K-COL-06-T", КН.температура_нейтралі(E, F, драп=dict(метал="золото", нейтралі="теплі"), речі=[р])),
                  ("R-COL-16", КН.бік_b_біля_обличчя(E, {}, _бб=dict(вхід=True, бік=-1, b_очей=-10, довіра=1)))):
        for x in з:
            ліч[ім + ":" + ("без входу" if x.get("без_входу") else x["сила"])] += 1
    ліч["носій поля"] += А.носій_приобличчевого_поля([р]) is not None
    ліч["місце невідоме"] += М.бік_межі(р) is None
print(json.dumps(dict(sorted(ліч.items())), ensure_ascii=False, indent=2))
тимчасова.cleanup()
