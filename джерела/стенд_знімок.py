# -*- coding: utf-8 -*-
"""ЗНІМОК СТЕНДА: числа, за якими видно, що змінилось у системі.

Прогін офлайн і детермінований: `ліміт_фото` за замовчуванням 0, тож колір
береться з вікна назви (впевненість 0.35), мережа не потрібна, і два прогони на
тому самому коді дають байт-у-байт той самий знімок.

Не тест «впало / не впало». Тест такого роду не ловить головного дефекту цієї
системи — правило, яке тихо перестало спрацьовувати, бо поле не доїхало. Тому
знімок міряє СПРАЦЮВАННЯ: які ID правил вийшли, скільки разів, з якою силою, у
якому відрі. Порівняння двох знімків показує, що саме зникло або зʼявилось.

Прогін:  python3 знімок.py [ім'я_знімка]
Порівняння: python3 знімок.py --діф база нове
"""
import sys, os, json, collections

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ТУТ)
os.chdir(ТУТ)

# КАТАЛОГ ЛЕЖИТЬ У РЕПОЗИТОРІЇ СТИСНУТИЙ (44 МБ розпакований). Розпаковується
# один раз поруч зі знімком: тримати в git 44 МБ, які відновлюються за секунду,
# нема сенсу, а вимагати ручного кроку перед прогоном — значить готувати
# «стенд не запускається».
_GZ = os.path.join(ТУТ, "..", "каталог_повний.xml.gz")
КАТАЛОГ = os.path.join(ТУТ, "каталог_повний.xml")
if not os.path.exists(КАТАЛОГ) and os.path.exists(_GZ):
    import gzip, shutil
    with gzip.open(_GZ, "rb") as _вх, open(КАТАЛОГ, "wb") as _вих:
        shutil.copyfileobj(_вх, _вих)

СЦЕНАРІЇ = {
    "офіс·18°C": dict(нагода="робота", місце="офіс", година=9, темп_c=18,
                      дрес_код="business_casual"),
    "спека·парк": dict(нагода="щоденне", місце="парк", година=15, темп_c=31),
    "дощ·ресторан·вечір": dict(нагода="побачення", місце="ресторан", година=20,
                               темп_c=5, опади="дощ", вітер=8, реагенти="так"),
    "весілля·гість": dict(нагода="весілля_гість", місце="весілля_вечірнє",
                          година=17, темп_c=24),
}


def _знахідки_рекурсивно(o, шлях=""):
    """Усі dict-и, що виглядають як знахідка, де б вони не лежали у виході.

    Свідомо обходить УСЕ дерево, а не перелік ключів: сенс знімка в тому, щоб
    побачити знахідку, яку хтось загубив у ручному переліку відер.
    """
    out = []
    if isinstance(o, dict):
        if "правило" in o and ("суть" in o or "чому" in o):
            out.append((шлях, o))
        else:
            for k, v in o.items():
                out += _знахідки_рекурсивно(v, шлях + "/" + str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            out += _знахідки_рекурсивно(v, шлях)
    return out


def прогін(назва, сцен):
    import bridge as B, trace as СЛ
    вх = json.load(open("стенд_вх.json"))
    вх["сценарій"] = сцен
    вх["випадок"] = назва
    СЛ.почати()
    r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    if r.get("помилка"):
        return dict(помилка=r["помилка"])
    к = r.get("кандидати") or {}
    слід = СЛ.зібрати()
    з = _знахідки_рекурсивно(r)
    return dict(
        пул=r.get("пул_речей"),
        кандидати={k: len(v) for k, v in к.items()},
        відсічено=(r.get("відсічено") or {}).get("лічба") or {},
        слоти_випали=sorted(r.get("слоти_випали") or []),
        руки={k: len(v) for k, v in (r.get("руки") or {}).items()},
        правила_брифа=sorted({p.get("код") for p in (r.get("правила") or []) if p.get("код")}),
        слід_ід=sorted(СЛ.ід_у_сліді()) if hasattr(СЛ, "ід_у_сліді") else [],
        слід_лічба=len(слід.get("записи", []) if isinstance(слід, dict) else слід or []),
        знахідки_шляхи=sorted(collections.Counter(ш for ш, _ in з).items()),
        знахідки_правила=sorted(collections.Counter(
            z.get("правило") for _, z in з).items()),
    )


def образ_і_суд(назва, сцен):
    """Другий бік: узяти детермінований образ із пулу і віддати його судові.

    Саме тут живуть відра `pipeline.перевірити_образ`, і саме тут видно, які з
    них доходять до виходу.
    """
    import bridge as B, pipeline as PL, composer as КМ, fit as ПС
    вх = json.load(open("стенд_вх.json"))
    вх["сценарій"] = сцен
    вх["випадок"] = назва
    r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    if r.get("помилка"):
        return dict(помилка=r["помилка"])
    к = r.get("кандидати") or {}
    речі = []
    for слот in ("верх", "низ", "взуття", "сумка"):
        пул = к.get(слот) or []
        if пул:
            речі.append(dict(пул[0], слот=слот))
    if len(речі) < 2:
        return dict(помилка="замало кандидатів")
    T = ПС.тіло(float(вх["зріст"]), {k: float(v) for k, v in вх["обхвати"].items()})
    import colorspace as cs
    F = cs.features(cs.hx(вх["шкіра"]), cs.hx(вх["волосся"][0]), cs.hx(вх["очі"]))
    готові = [КМ._у_річ(dict(c), c["слот"], T) for c in речі]
    вих = PL.перевірити_образ(F, готові, тіло=T, **сцен)
    з = _знахідки_рекурсивно(вих)
    return dict(
        речей=len(готові),
        ключі_виходу=sorted(вих.keys()),
        знахідки_шляхи=sorted(collections.Counter(ш for ш, _ in з).items()),
        знахідки_правила=sorted(collections.Counter(z.get("правило") for _, z in з).items()),
        сили=sorted(collections.Counter(str(z.get("сила")) for _, z in з).items()),
        блокує=sum(1 for _, z in з if z.get("блокує")),
        чеклісти=json.loads(json.dumps(вих.get("чеклісти"), ensure_ascii=False, default=str))
        if вих.get("чеклісти") else None,
        припущень=len(вих.get("припущення") or []),
    )


def знімок():
    out = {}
    for назва, сцен in СЦЕНАРІЇ.items():
        out[назва] = dict(запити=прогін(назва, сцен), суд=образ_і_суд(назва, сцен))
    return out


def діф(a, b):
    """Що зникло, що зʼявилось, що змінило число."""
    рядки = []

    def обхід(x, y, шлях):
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y)):
                обхід(x.get(k), y.get(k), шлях + "/" + str(k))
        elif isinstance(x, list) and isinstance(y, list):
            sx = {json.dumps(i, ensure_ascii=False, sort_keys=True) for i in x}
            sy = {json.dumps(i, ensure_ascii=False, sort_keys=True) for i in y}
            for i in sorted(sx - sy):
                рядки.append("− %s  %s" % (шлях, i))
            for i in sorted(sy - sx):
                рядки.append("+ %s  %s" % (шлях, i))
        elif x != y:
            рядки.append("≠ %s  %r → %r" % (шлях, x, y))

    обхід(a, b, "")
    return рядки


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--діф":
        a = json.load(open(sys.argv[2], encoding="utf-8"))
        b = json.load(open(sys.argv[3], encoding="utf-8"))
        d = діф(a, b)
        print("\n".join(d) if d else "знімки збігаються")
        sys.exit(0)
    імʼя = sys.argv[1] if len(sys.argv) > 1 else "знімок"
    s = знімок()
    json.dump(s, open(імʼя + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True, default=str)
    for сц, d in s.items():
        з = d["запити"]
        c = d["суд"]
        print("── %s" % сц)
        if з.get("помилка"):
            print("   запити ПОМИЛКА: %s" % з["помилка"]); continue
        print("   пул %s · кандидатів %d · правил у брифі %d · слід %d"
              % (з["пул"], sum(з["кандидати"].values()), len(з["правила_брифа"]),
                 з["слід_лічба"]))
        if c.get("помилка"):
            print("   суд ПОМИЛКА: %s" % c["помилка"])
        else:
            print("   суд: знахідок %d по %d правилах · блокує %d · припущень %d"
                  % (sum(n for _, n in c["знахідки_правила"]),
                     len(c["знахідки_правила"]), c["блокує"], c["припущень"]))
    print("\nзаписано %s.json" % імʼя)
