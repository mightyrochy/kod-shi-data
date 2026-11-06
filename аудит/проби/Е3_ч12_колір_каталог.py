# -*- coding: utf-8 -*-
"""Е3-одна-величина ч12 (п.2, колір): каталог ДО → ПІСЛЯ за кожним зміненим порівнянням.

Запуск із кореня репозиторію:
    python3 аудит/проби/Е3_ч12_колір_каталог.py                       # ПІСЛЯ: код цієї гілки
    git worktree add /tmp/до <SHA_ДО>
    python3 аудит/проби/Е3_ч12_колір_каталог.py --код /tmp/до/джерела  # ДО: той самий скрипт на старому коді

Каталог — `джерела/каталог_повний.xml` цього клону (один для ДО й ПІСЛЯ), через
`bridge.виклик("запити")` стенда; модель і платні API не викликаються. Друкує:
  K-COL-06  `колір_річ.нейтраль` (межа боку b* `b_нейтралі`) — лічба класів речей каталогу;
  R-COL-16  `палітра_нейтраль.бік_b_речі` — лічба боків b* речей;
  K-KOH-08  `формальність.майже_біла_річ` (вікно `біле_вікно`) — лічба речей;
  K-ACC-10  клас `distinct` пар виміряних кольорів (поріг, яким його питає `надточний_збіг`) — лічба вердиктів;
  K-PAL-02  `колір_відношення.сила_відлуння_очей` речей × райдужок — лічба вердиктів зрізом 0.5;
  R-COL-16 / K-CLR-01  бік очей (`face_features.ознаки`) і рядок «температура» рангу основ (`bases.ранг`)
            на райдужках ручного входу й фото (`--очі` — лише ці рядки)."""
import sys, pathlib, json, collections, os, io, contextlib, itertools, random

КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
код = pathlib.Path(sys.argv[sys.argv.index("--код") + 1]).resolve() if "--код" in sys.argv else КОРІНЬ / "джерела"
os.chdir(код); sys.path.insert(0, str(код))
import feed as Ф, bridge as B, colorspace as cs, колір_річ as КР, палітра_нейтраль as ПН, формальність as ФМ
import колір_відношення as КВ, face_features as ОБ, bases as БС, міст_основи as МО
from реєстр_правил import C

ОЧІ = ["#5a3a1e", "#7fa8d8", "#759087", "#6b8cae", "#4a3527", "#8a7a5a", "#3b5b7a", "#6e6e60",
       "#a0886a", "#5f7f6a", "#9aa7b0", "#7a6040"]
ЛИШЕ_ОЧІ = "--очі" in sys.argv   # лише рядки R-COL-16 / K-CLR-01 (без каталогу)
if not ЛИШЕ_ОЧІ:
 вх = json.load(open(код / "стенд_вх.json", encoding="utf-8")); вх["гілка"] = 0
 вх["каталог"] = Ф.каталог_на_диску(str(КОРІНЬ / "джерела" / "каталог_повний.xml"))
 with contextlib.redirect_stdout(io.StringIO()):
     json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
 кат = B.каталог_останнього_пакета()
 виміри = [c for c in кат if КР.межі_кольору(c) is not None and КР.не_вимір(c) is None]
 print("речей у пулі:", len(кат), "· з виміряним кольором:", len(виміри))

 лаб = lambda c: КР.точка_кольору(c)
 print("K-COL-06 нейтраль:", dict(collections.Counter(КР.нейтраль(лаб(c)) for c in виміри)))
 print("R-COL-16 бік_b_речі:", dict(collections.Counter(ПН.бік_b_речі(лаб(c)) for c in виміри)))
 print("K-KOH-08 майже_біла_річ:", dict(collections.Counter(ФМ.майже_біла_річ(c) for c in кат)))

 random.seed(12)
 пари = random.sample(list(itertools.combinations(виміри, 2)), 20000)
 import аксесуари_реєстр as АР
 поріг = АР.C.get("ΔE_точний_збіг", АР.C["ΔE_шум_фото"])   # ПІСЛЯ запису нема — поріг «distinct» = шум фото
 print("K-ACC-10 distinct (поріг %.1f, 20000 пар, seed 12):" % поріг,
       dict(collections.Counter(КР.відношення(a, b, "distinct", поріг=поріг) for a, b in пари)))

 записи = [КР.запис_кольору(c) for c in виміри[:3000]]
 відлуння = collections.Counter()
 for о in ОЧІ:
     оч = КР.запис_кольору(dict(lab=tuple(cs.hx(о))))
     for р in записи:
         відлуння[КВ.вердикт(КВ.сила_відлуння_очей(р, оч))] += 1
 print("K-PAL-02 відлуння очей (12 райдужок × 3000 речей):", dict(відлуння))

ШК, ВЛ = "#e8c4ad", "#5a4636"
for дж in (None, "uncontrolled"):
    бік, темп = collections.Counter(), collections.Counter()
    for о in ОЧІ:
        F = cs.features(cs.hx(ШК), cs.hx(ВЛ), cs.hx(о), **({"джерело": дж} if дж else {}))
        if дж:   # фото: протокол і позначка фото в `_meta`, як їх ставить шлях фото
            F["_meta"] = dict(F.get("_meta") or {}, from_photo=True, protocol=дж)
        б = ОБ.ознаки(F)["бік_очей"]
        бік[(б.get("вхід"), б.get("бік"))] += 1
        with contextlib.redirect_stdout(io.StringIO()):
            о_ = МО.основи(F, **({"source": дж} if дж else {}))
        рядки = о_.get("рекомендовані") or []
        темп["температура в «чому»" if any("температура" in (r.get("чому") or "") for r in рядки) else "без"] += 1
    print("R-COL-16 бік очей, вхід %s:" % (дж or "ручний hex"), dict(бік))
    print("K-CLR-01 рядок температури рангу основ, вхід %s:" % (дж or "ручний hex"), dict(темп))
