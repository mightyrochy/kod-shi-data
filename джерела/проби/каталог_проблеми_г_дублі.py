# -*- coding: utf-8 -*-
"""Рядок 5627 (реєстр 5616, клас Г8): одна річ крамниці — кілька записів каталогу. Факт: групи з тією самою назвою,
кольором і крамницею; записи з розміром у назві «(11, S, …)» (оферта на розмір); групи `group_id`; пари записів з
однаковим першим знімком під різними назвами (дві мовні версії сторінки). Запуск: python3 джерела/проби/каталог_проблеми_г_дублі.py"""
import collections, gzip, os, re                                               # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
def запис(о):
    п = lambda ім: (re.findall(r'<param name="%s">([^<]*)<' % ім, о) or [""])[0]   # noqa: E731
    return {"назва": re.search(r"<name>([^<]*)<", о).group(1), "м": п("магазин"), "колір": п("Колір"),
            "фото": re.findall(r"<picture>([^<]*)<", о), "url": re.search(r"<url>([^<]*)<", о).group(1)}
зз = [запис(о) for о in re.findall(r"<offer\b.*?</offer>", xml, re.S)]
гр = collections.Counter((з["м"], з["назва"], з["колір"]) for з in зз)
д = {к: ч for к, ч in гр.items() if ч > 1}
print("записів %d · груп «та сама крамниця+назва+Колір» %d, у них записів %d (зайвих %d) · %s" % (len(зз), len(д),
      sum(д.values()), sum(д.values()) - len(д), collections.Counter(к[0] for к in д).most_common(5)))
розм = [з for з in зз if re.search(r"\(\s*\d+\s*,\s*(XXS|XS|S|M|L|XL|XXL|\d\d)\s*,", з["назва"])]
print("назва з розміром варіанта «(N, S, …)»: %d · %s" % (len(розм), collections.Counter(з["м"] for з in розм).most_common(4)))
url = collections.Counter(з["url"] for з in зз)
print("той самий url у кількох записах: %d url, %d записів" % (sum(1 for ч in url.values() if ч > 1), sum(ч for ч in url.values() if ч > 1)))
перше = collections.defaultdict(set)
for з in зз:
    if з["фото"]:
        перше[(з["м"], re.sub(r"\?.*", "", з["фото"][0]).rsplit("/", 1)[-1])].add(з["назва"])
мови = [(к, н) for к, н in перше.items() if len(н) == 2 and sum(1 for х in н if not re.search(r"[а-яіїєґ]", х.lower())) == 1]
print("перший знімок спільний рівно для двох назв, одна з них без кирилиці (мовні двійники): %d · %s · %s" % (len(мови),
      collections.Counter(к[0] for к, _ in мови).most_common(4), [sorted(н) for _, н in мови[:1]]))
