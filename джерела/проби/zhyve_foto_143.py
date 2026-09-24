# -*- coding: utf-8 -*-
"""Рядок 143: скільки карток ідуть БЕЗ ЖИВОГО ФОТО — до і після, по крамницях.
«ДО» — відбір із вимкненими правками 23.09 (ключ знімка, `https`, заглушка, форма, дозвіл
крамниці) і БЕЗ переходу на наступний кадр; «ПІСЛЯ» — нинішній плюс `показ.html:
підставитиКадр`, тобто мертва лише річ, у якої не відкривається ЖОДЕН кадр ряду.
ЖИВИЙ = 200/206 І СИГНАТУРА КАРТИНКИ в тілі: alot на кожну адресу фото віддає HTML із кодом
200 (браузер ріже `ERR_BLOCKED_BY_ORB`), musthave — 206 без `Content-Type`, але з живим
WEBP; ні код, ні заголовок поодинці цих двох не розрізняють.
Запуск: PYTHONPATH=. python3 проби/zhyve_foto_143.py [речей на крамницю = 6]"""
import collections, os, re, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф, фід_фото as ФФ; N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
оф = Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"))[0]
зб, крам, сп, хо = Ф.читати_збагачення(), collections.defaultdict(list), ФФ._спільні_фото, ФФ._хости_крамниць
for o in sorted(оф, key=lambda x: x["id"]): крам[o.get("магазин")].append(o)
вибір = [o for с in крам.values() for o in с[:N]]
ряд = lambda o: ФФ.кадри_речі(o, сп(оф).get(o.get("магазин")) or {}, хо(оф), (зб.get(o["id"]) or {}).get("фото"))
ПІС, ПІДПИСИ = {o["id"]: ряд(o) for o in вибір}, (b"\xff\xd8", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"<?xml", b"<svg")
СЕГ, ХВ = ФФ._РОЗМІР_СЕГМЕНТ, ФФ._РОЗМІР_ХВІСТ   # ↓ латка «ДО»: ключ і правила до 23.09
ФФ._файл_фото = lambda u: ХВ.sub("", "/".join(c for c in str(u or "").split("?")[0].split("/")[3:] if not СЕГ.match(c))).lower()
ФФ.ЗАГЛУШКА_ІМЕНІ, ФФ.не_покаже_браузер, ФФ._на_https, ФФ._форма_меншини = re.compile(r"(?!)"), (lambda u, х=None: None), (lambda u: u), (lambda к: set())
ФФ.ПОЛЕ_ВІДНОВЛЕНІ = "_поля_нема_"             # шосте правило (рядки 168/169) — теж після 23.09
ДО = {o["id"]: ряд(o)[:1] for o in вибір}      # один кадр: переходу на наступний доти не було
адреси = sorted({u for р in list(ДО.values()) + list(ПІС.values()) for u in р})
def живий(u):
    """Чи відкриється адреса як КАРТИНКА: код І сигнатура тіла, не заголовок."""
    ч = urllib.parse.urlsplit(u)
    з = urllib.request.Request(ч._replace(path=urllib.parse.quote(ч.path, safe="/%~")).geturl(),
        headers={"User-Agent": "Mozilla/5.0 Chrome/131", "Range": "bytes=0-31"})
    try: в = urllib.request.urlopen(з, timeout=25); б = в.read(32)
    except Exception: return False           # мережа: будь-який збій = не живий
    return в.status in (200, 206) and (б.startswith(ПІДПИСИ) or б[4:12] in (b"ftypavif", b"ftypheic") or (б[:4] == b"RIFF" and б[8:12] == b"WEBP"))
with ThreadPoolExecutor(40) as п: жив = dict(zip(адреси, п.map(живий, адреси)))
с = collections.Counter((o.get("магазин"), м) for o in вибір for м, р in
    (("ДО", ДО[o["id"]]), ("ПІСЛЯ", ПІС[o["id"]])) if not any(жив.get(u) for u in р))
р = lambda м: sum(v for k, v in с.items() if k[1] == м)
print("вибірка %d речей (до %d на крамницю) з %d · крамниць %d · адрес %d\nБЕЗ ЖИВОГО ФОТО РАЗОМ: ДО %d → ПІСЛЯ %d"
      % (len(вибір), N, len(оф), len(крам), len(адреси), р("ДО"), р("ПІСЛЯ")))
for м in sorted((м for м in крам if с[(м, "ДО")] or с[(м, "ПІСЛЯ")]), key=lambda м: (-с[(м, "ДО")], м)):
    print("  %-22s з %2d речей · ДО %2d · ПІСЛЯ %2d" % (м, len(крам[м][:N]), с[(м, "ДО")], с[(м, "ПІСЛЯ")]))
