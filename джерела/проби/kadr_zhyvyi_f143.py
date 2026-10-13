# -*- coding: utf-8 -*-
"""Ф-143: карток вибірки з ЖИВИМ ВЛАСНИМ кадром — до і після, по крамницях.
ДО — картка стоїть на ПЕРШОМУ кадрі (так було до ланцюга рядка 143 — і так само вона стоїть
на кадрі, що МОВЧИТЬ: без годинника Ф-143 `підставитиКадр` з нього не зрушує); ПІСЛЯ — весь
ряд `фід_фото.кадри_речі`. ЖИВИЙ — код 200/206 І СИГНАТУРА КАРТИНКИ в тілі (alot віддає HTML
із кодом 200, musthave — 206 без `Content-Type`). ЧУЖИЙ ПЕРШИМ — заглушка, спільна картинка крамниці або інша форма кадру
(таблиця розмірів); кадр ЖНИВ інакшої форми чужим не рахується — першість він виграє
навмисно (правило 2 `кадри_речі`). Таймаут 6 с: `zhyve_foto_143.py` двічі впала ~200 с.
Запуск: PYTHONPATH=. python3 проби/kadr_zhyvyi_f143.py [речей на крамницю = 6]"""
import collections, os, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф, фід_фото as ФФ; N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
оф = Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"))[0]
зб, крам, сп, хо = Ф.читати_збагачення(), collections.defaultdict(list), ФФ._спільні_фото, ФФ._хости_крамниць
for o in sorted(оф, key=lambda x: x["id"]): крам[o.get("магазин")].append(o)
сп, хо = сп(оф), хо(оф); вибір = [o for с_ in крам.values() for o in с_[:N]]
жнив = {o["id"]: (зб.get(o["id"]) or {}).get("фото") for o in вибір}
ряд = {o["id"]: ФФ.кадри_речі(o, сп.get(o.get("магазин")) or {}, хо, жнив[o["id"]]) for o in вибір}
ПІДПИСИ = (b"\xff\xd8", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"<?xml", b"<svg")
def живий(u):
    """Чи відкриється адреса як КАРТИНКА: код І сигнатура тіла, не заголовок."""
    ч = urllib.parse.urlsplit(u)
    з = urllib.request.Request(ч._replace(path=urllib.parse.quote(ч.path, safe="/%~")).geturl(),
        headers={"User-Agent": "Mozilla/5.0 Chrome/131", "Range": "bytes=0-31"})
    try: в = urllib.request.urlopen(з, timeout=6); б = в.read(32)
    except Exception: return False           # мережа: будь-який збій = не живий
    return в.status in (200, 206) and (б.startswith(ПІДПИСИ) or б[4:12] in (b"ftypavif", b"ftypheic")
                                       or (б[:4] == b"RIFF" and б[8:12] == b"WEBP"))
адреси = sorted({u for р in ряд.values() for u in р})
with ThreadPoolExecutor(24) as п: жив = dict(zip(адреси, п.map(живий, адреси)))
чуж = lambda o, р: bool(р) and bool(ФФ.заглушка_кадру(р[0])
    or ФФ.спільна_картинка(ФФ._файл_фото(р[0]), сп.get(o.get("магазин")) or {})
    or (0 in ФФ._форма_меншини(р) and ФФ._файл_фото(р[0]) != ФФ._файл_фото(жнив[o["id"]] or "")))
с = collections.Counter()
for o in вибір:
    м, р = o.get("магазин"), ряд[o["id"]]
    с[(м, "речей")] += 1; с[(м, "нема")] += (not р); с[(м, "чуж")] += чуж(o, р)
    с[(м, "ДО")] += bool(р and жив.get(р[0])); с[(м, "ПІСЛЯ")] += any(жив.get(u) for u in р)
р_ = lambda к: sum(v for (_, к2), v in с.items() if к2 == к)
print("вибірка %d речей (до %d на крамницю) з %d · крамниць %d · адрес %d\nЖИВИЙ ВЛАСНИЙ КАДР: ДО %d "
      "(%.1f %%) → ПІСЛЯ %d (%.1f %%) · кадрів нема в %d · ЧУЖИЙ ПЕРШИМ %d" % (len(вибір), N, len(оф),
      len(крам), len(адреси), р_("ДО"), 100.0*р_("ДО")/len(вибір), р_("ПІСЛЯ"), 100.0*р_("ПІСЛЯ")/len(вибір),
      р_("нема"), р_("чуж")))
for м in sorted(крам, key=lambda м: (с[(м, "ПІСЛЯ")] - с[(м, "речей")], м)):
    if с[(м, "ПІСЛЯ")] < с[(м, "речей")] or с[(м, "ДО")] < с[(м, "ПІСЛЯ")] or с[(м, "чуж")]:
        print("  %-24s з %2d: ДО %2d · ПІСЛЯ %2d · кадрів нема %d · чужий першим %d"
              % (м, с[(м, "речей")], с[(м, "ДО")], с[(м, "ПІСЛЯ")], с[(м, "нема")], с[(м, "чуж")]))
