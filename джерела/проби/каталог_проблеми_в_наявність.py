# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «мертві посилання й наявність». ФАКТ: (1) дата
# знімання (`param знято`) і вік каталогу на сьогодні; (2) оферів available=false у файлі
# (пул їх відсіює, `композитор_придатні`); (3) ВИБІРКА живих сторінок (аргумент N, типово 0 —
# без мережі; 200 — як у реєстрі): код відповіді, переадресація на розділ чи головну,
# schema.org `availability` OutOfStock на сторінці. Мережа — лише за явним N.
import os, re, sys, random, datetime, urllib.request, urllib.parse, collections as C
import concurrent.futures as КФ
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed
оф = feed.читати_yml(feed.каталог_на_диску())[0]
дати = C.Counter((o.get("параметри") or {}).get("знято") for o in оф)
стар = min(d for d in дати if d)
print("знято: %s · найстаріше %s — %d днів тому" % (dict(дати), стар,
      (datetime.date.today() - datetime.date.fromisoformat(стар)).days))
print("оферів %d · available=false %d · невідомо %d" % (len(оф), sum(1 for o in оф if o["available"] is False),
                                                       sum(1 for o in оф if o["available"] is None)))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 0
random.seed(15)
ДОСТ = re.compile(r'(?:schema\.org/|"availability"\s*:\s*")(InStock|OutOfStock|SoldOut|Discontinued)', re.I)
def глянути(o):
    """(код, переадресовано, {стан schema.org}) однієї сторінки товару."""
    try:
        в = urllib.request.urlopen(urllib.request.Request(o["url"], headers={"User-Agent": "Mozilla/5.0"}), timeout=20)
        т = в.read(600000).decode("utf-8", "ignore")
        шлях = lambda u: urllib.parse.urlparse(u).path.rstrip("/")
        return в.status, шлях(в.geturl()) != шлях(o["url"]), {x.lower() for x in ДОСТ.findall(т)}
    except urllib.error.HTTPError as п:
        return п.code, False, set()
    except OSError as п:
        return "мережа: " + type(п).__name__, False, set()
if N:
    with КФ.ThreadPoolExecutor(8) as пул:
        в = list(пул.map(глянути, random.sample([o for o in оф if o["available"]], N)))
    print("вибірка %d «є в наявності»: коди %s · переадресовано на інше %d · розмітка є %d, з них "
          "лише OutOfStock/SoldOut %d" % (N, dict(C.Counter(x[0] for x in в)), sum(1 for x in в if x[1]),
          sum(1 for x in в if x[2]), sum(1 for x in в if x[2] and "instock" not in x[2])))
