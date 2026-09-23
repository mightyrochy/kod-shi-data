# -*- coding: utf-8 -*-
"""Рядок 143: скільки карток ідуть БЕЗ ЖИВОГО ФОТО — до і після, по крамницях.
«ДО» — відбір із вимкненими правками 23.09 (ключ знімка, `https`, заглушка, форма
кадру, дозвіл крамниці) і БЕЗ переходу на наступний кадр; «ПІСЛЯ» — нинішній плюс
`показ.html: підставитиКадр`, тобто мертва лише річ, у якої не відкривається ЖОДЕН
кадр ряду. Живий = HTTP 200/206, шлях екранується, як браузер.
Запуск: PYTHONPATH=. python3 проби/zhyve_foto_143.py [речей на крамницю = 6]"""
import collections, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф, фід_фото as ФФ
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
оф = Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"))[0]
зб, крам = Ф.читати_збагачення(), collections.defaultdict(list)
for o in sorted(оф, key=lambda x: x["id"]): крам[o.get("магазин")].append(o)
вибір, сп, хо = [o for с in крам.values() for o in с[:N]], ФФ._спільні_фото, ФФ._хости_крамниць
ряд = lambda o: ФФ.кадри_речі(o, сп(оф).get(o.get("магазин")) or {}, хо(оф), (зб.get(o["id"]) or {}).get("фото"))
ПІС = {o["id"]: ряд(o) for o in вибір}
СЕГ, ХВ = ФФ._РОЗМІР_СЕГМЕНТ, ФФ._РОЗМІР_ХВІСТ           # ключ, який стояв до 23.09
ФФ._файл_фото = lambda u: ХВ.sub("", "/".join(
    c for c in str(u or "").split("?")[0].split("/")[3:] if not СЕГ.match(c))).lower()
ФФ.ЗАГЛУШКА_ІМЕНІ, ФФ.ХОСТИ_БЕЗ_ЧУЖОГО_ПОКАЗУ = re.compile(r"(?!)"), ()
ФФ._на_https, ФФ._форма_меншини = (lambda u: u), (lambda к: set())
ДО = {o["id"]: ряд(o)[:1] for o in вибір}
адреси = sorted({u for р in list(ДО.values()) + list(ПІС.values()) for u in р})
def код(u):
    """HTTP-код адреси; будь-який мережевий збій — теж відповідь: кадр не живий."""
    ч = urllib.parse.urlsplit(u)
    з = urllib.request.Request(ч._replace(path=urllib.parse.quote(ч.path, safe="/%~")).geturl(),
        headers={"User-Agent": "Mozilla/5.0 Chrome/131", "Range": "bytes=0-0"})
    try: return urllib.request.urlopen(з, timeout=25).status
    except Exception as e: return getattr(e, "code", -1)
with ThreadPoolExecutor(40) as п: жив = dict(zip(адреси, (k in (200, 206) for k in п.map(код, адреси))))
с = collections.Counter((o.get("магазин"), м) for o in вибір for м, р in
    (("ДО", ДО[o["id"]]), ("ПІСЛЯ", ПІС[o["id"]])) if not any(жив.get(u) for u in р))
print("вибірка %d речей (до %d на крамницю) з %d · крамниць %d · адрес перевірено %d\n"
      "БЕЗ ЖИВОГО ФОТО РАЗОМ: ДО %d → ПІСЛЯ %d" % (len(вибір), N, len(оф), len(крам), len(адреси),
      sum(v for k, v in с.items() if k[1] == "ДО"), sum(v for k, v in с.items() if k[1] == "ПІСЛЯ")))
for м in sorted((м for м in крам if с[(м, "ДО")] or с[(м, "ПІСЛЯ")]), key=lambda м: (-с[(м, "ДО")], м)):
    print("  %-22s з %2d речей · ДО %2d · ПІСЛЯ %2d" % (м, len(крам[м][:N]), с[(м, "ДО")], с[(м, "ПІСЛЯ")]))
