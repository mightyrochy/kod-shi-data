# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «бренд». ФАКТ: (1) у СИРОМУ архіві — скільки
# оферів несуть `<vendor>`, скільки лише характеристику картки `~бренд`, скільки нічого;
# (2) скільки різних брендів і скільки оферів, де бренд = ім'я самої крамниці; (3) «(Other
# Brand)» — у `<vendor>` і в назві (п.21: це справжній бренд); (4) чи доходить бренд до
# розібраного офера фіду (ключі офера) — тобто чи може він дійти до запису речі.
import os, re, sys, gzip, collections as C
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed
архів = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(feed.каталог_на_диску()), os.pardir, "каталог_повний.xml.gz")
офери = re.findall(r"<offer\b.*?</offer>", gzip.open(архів, "rt", encoding="utf-8").read(), re.S)
поле = lambda o, rx: (re.search(rx, o) or [None, ""])[1].strip()
в = [(поле(o, r"<vendor>([^<]*)</vendor>"), поле(o, r'<param name="~бренд">([^<]*)</param>'),
      поле(o, r"<url>https?://(?:www\.)?([^/.<]+)"), поле(o, r"<name>([^<]*)</name>")) for o in офери]
print("оферів %d · <vendor> %d · лише ~бренд %d · без бренду %d"
      % (len(в), sum(1 for x in в if x[0]), sum(1 for x in в if not x[0] and x[1]),
         sum(1 for x in в if not x[0] and not x[1])))
бр = C.Counter((x[0] or x[1]) for x in в if x[0] or x[1])
свій = sum(1 for x in в if (x[0] or x[1]) and re.sub(r"\W", "", (x[0] or x[1]).lower()) in
           re.sub(r"\W", "", x[2].lower()))
print("різних брендів %d · бренд = ім'я крамниці %d · найчастіші %s" % (len(бр), свій, бр.most_common(5)))
print("«Other Brand»: у <vendor> %d · у назві %d" % (sum(1 for x in в if "other brand" in x[0].lower()),
                                                   sum(1 for x in в if "other brand" in x[3].lower())))
кр = C.defaultdict(lambda: [0, 0])                 # крамниця → [оферів, з брендом]
for o, x in zip(офери, в):
    к = кр[(re.search(r"<url>https?://(?:www\.)?([^/<]+)", o) or [None, "?"])[1]]
    к[0] += 1; к[1] += bool(x[0] or x[1])
без = sorted(((k, v[0]) for k, v in кр.items() if not v[1]), key=lambda x: -x[1])
print("крамниць %d · без бренду в жодному офері %d · змішаних %d · найбільші безбрендові: %s"
      % (len(кр), len(без), sum(1 for v in кр.values() if 0 < v[1] < v[0]), без[:5]))
оф = feed.читати_yml(feed.каталог_на_диску())[0]
ключі = {k for o in оф for k in o} | {k for o in оф for k in (o.get("параметри") or {})}
print("ключ бренду в розібраному офері фіду: %s" % (sorted(k for k in ключі if re.search("vendor|бренд", k)) or "нема"))
