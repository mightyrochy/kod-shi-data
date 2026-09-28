# -*- coding: utf-8 -*-
"""HTML-сутність у тексті крамниці: скільки речей каталогу її несли й скільки несуть після входу.
ДО — сирий архів каталогу як є; ПІСЛЯ — те, що з нього робить вхід каталогу (`чистка_каталогу`).
Запуск: cd джерела && python3 проби/nazvy_smittia_feedu.py"""
import collections, gzip, html, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import чистка_каталогу as ЧК

АРХІВ = next(ш for ш in (os.path.join(ТУТ, "..", "каталог_повний.xml.gz"),
                         os.path.join(ТУТ, "каталог_повний.xml.gz")) if os.path.exists(ш))
сирий = gzip.open(АРХІВ, "rt", encoding="utf-8").read()
оферів = [м.group(0) for м in ЧК._OFFER.finditer(сирий)]
чисті = [ЧК._розекранувати_сире(т) for т in оферів]
print("ФАКТ · оферів в архіві %d · несуть екрановану HTML-сутність: ДО %d → ПІСЛЯ %d · шарів знято %d"
      % (len(оферів), sum(1 for _, n in чисті if n),
         sum(1 for т, _ in чисті if ЧК._розекранувати_сире(т)[1]), sum(n for _, n in чисті)))

# ЯКІ САМЕ СУТНОСТІ — поіменно: дві з них (СТАРІ) знімались і доти, решта доїжджала
# до жінки видимим текстом («В&#8217;язаний снуд з бавовни»).
СТАРІ = ("&amp;quot;", "&amp;amp;")
лічба = collections.Counter(ЧК._СУТНІСТЬ.findall(сирий))
поіменно = sorted(((("&amp;%s;" % к), n) for к, n in лічба.items()), key=lambda x: -x[1])
print("ФАКТ · сутності поіменно: %s" % ", ".join("%s %d" % (к, n) for к, n in поіменно[:10]))
print("ФАКТ · з них знімались і ДО цієї гілки: %d · знімаються лише тепер: %d"
      % (sum(n for к, n in поіменно if к in СТАРІ), sum(n for к, n in поіменно if к not in СТАРІ)))

_МАГ = re.compile(r'<param name="магазин">([^<]*)</param>')
по_крамницях = collections.Counter()
for т, n in zip(оферів, (n for _, n in чисті)):
    if n:
        м = _МАГ.search(т)
        по_крамницях[м.group(1) if м else "?"] += 1
print("ФАКТ · речей із сутністю по крамницях (топ-8 із %d): %s"
      % (len(по_крамницях), ", ".join("%s %d" % (м, n) for м, n in по_крамницях.most_common(8))))

# СЛУЖБОВІ XML-СИМВОЛИ ЛИШАЮТЬСЯ ЕКРАНОВАНИМИ НА ОДИН ШАР — інакше файл перестав би бути XML.
проба = '<name>Штани &amp;amp;quot;Зозулька&amp;amp;quot; в&amp;#8217;язані</name>'
print("ФАКТ · %s → %s (після розбору: %s)"
      % (проба, ЧК._розекранувати_сире(проба)[0],
         html.unescape(re.sub(r"</?name>", "", ЧК._розекранувати_сире(проба)[0]))))
