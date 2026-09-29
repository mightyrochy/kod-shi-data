# -*- coding: utf-8 -*-
"""Проба РЗ-1: значення МОДЕЛІ ПОЗА ПЕРЕЛІКОМ на збережених відповідях прогону — друкує факт, моделі не кличе.
«До» — скільки значень не були кодом переліку дослівно; «після» — скільки з них лишились "unknown" попри
`каталог_розбір._звести` (розділовий знак схеми, пояснення в хвості, синонім коду). Обидві лічби — з `причини`
того самого `з_відповіді`, через яке йде `--зібрати`, тож повторне збирання дає ті самі числа. Праворуч у
рядку — найчастіше з того, що ЩЕ не зведено: це список, з якого росте мапа.
Запуск: python3 джерела/проби/каталог_розбір_поза_переліком.py [тека прогону …]"""
import collections, glob, os, re, sys, tarfile  # noqa: E401
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)  # noqa: E702
import каталог_розбір as КР  # noqa: E402
ЗВЕДЕНО, ПОЗА = re.compile(r"^(.+?): «(.*)» зведено до «(.+)»$"), re.compile(r"^(.+?): «(.*)» поза переліком$")
for т in sys.argv[1:] or sorted(glob.glob(os.path.join(Д, "..", "аудит", "розбір_каталогу", "*_uk*"))):
    тар, назва = os.path.join(т, "сирі_відповіді.tar.gz"), os.path.basename(os.path.normpath(т))
    if not os.path.exists(тар):
        print("%s · нема сирі_відповіді.tar.gz — лічба неможлива" % назва); continue  # noqa: E702
    а = tarfile.open(тар); зв, поза, речей, не_json = collections.Counter(), collections.defaultdict(collections.Counter), 0, 0  # noqa: E501,E702
    for ч in а:
        if not ч.isfile(): continue  # noqa: E701
        відп = а.extractfile(ч).read().decode("utf-8").replace("\r\n", "\n").partition("\n\n── ВІДПОВІДЬ")[2]
        поля, причини = КР.з_відповіді(відп); речей += 1; не_json += поля is None  # noqa: E702
        for п in причини:
            м = ЗВЕДЕНО.match(п)
            if м: зв[м.group(1)] += 1  # noqa: E701
            м = ПОЗА.match(п)
            if м: поза[м.group(1)][м.group(2)] += 1  # noqa: E701
    до = sum(зв.values()) + sum(sum(c.values()) for c in поза.values())
    після = sum(sum(c.values()) for c in поза.values())
    print("%s · речей %d · не JSON %d" % (назва, речей, не_json))
    нема = sum(к for c in поза.values() for з, к in c.items()
               if КР._вид(з) in КР._ВІДСУТНІСТЬ or КР._вид(з).startswith("no_"))
    print("  ПОЗА ПЕРЕЛІКОМ УСЬОГО: до %d -> після %d (зведено %d, %d %%)"
          % (до, після, до - після, round(100.0 * (до - після) / max(до, 1))))
    print("  з решти %d — слова відсутності («no», «none») на полях, де коду «того нема» в переліку"
          " НЕМА: чесне unknown, а не втрачений код" % нема)
    for поле in sorted(set(зв) | set(поза), key=lambda p: -(зв[p] + sum(поза[p].values()))):
        д, п = зв[поле] + sum(поза[поле].values()), sum(поза[поле].values())
        print("  %-22s до %5d -> після %5d | %s" % (поле, д, п, ", ".join(
            "%s×%d" % (з, к) for з, к in поза[поле].most_common(6))))
