# -*- coding: utf-8 -*-
"""Рядок 5624 (реєстр 5616, клас Г5): у кореневому каталозі — записи двох різних збирачів (складальник 07.09, якого
в репозиторії нема, і `виконавець.py` 18.09) з різними наборами полів. Факт: скільки записів кожного виду, які службові
поля є лише в одному виді й скільки комітів зробили каталог. Запуск: python3 джерела/проби/каталог_проблеми_г_формати.py"""
import collections, gzip, os, re, subprocess                                   # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
види = collections.defaultdict(list)
for о in re.findall(r"<offer\b.*?</offer>", xml, re.S):
    поля = set(re.findall(r'<param name="([^"~][^"]*)"', о))
    види["складальник 07.09" if "бал_інформації" in поля else "виконавець 18.09" if "канал" in поля else "інше"].append(поля)
частка = {в: collections.Counter(п for поля in з for п in поля) for в, з in види.items()}
for в, з in види.items():
    print("%-18s %5d записів · службових полів (без «~») різних %d" % (в, len(з), len(частка[в])))
а, б = list(частка)[:2]
лише = lambda х, у: sorted(п for п, ч in частка[х].items() if ч >= 0.5 * len(види[х]) and not частка[у].get(п))  # noqa: E731
print("поля в ≥50 %% записів «%s», яких нема в жодному «%s»: %s" % (а, б, лише(а, б)))
print("поля в ≥50 %% записів «%s», яких нема в жодному «%s»: %s" % (б, а, лише(б, а)))
лог = subprocess.run(["git", "-C", К, "log", "--format=%ad %s", "--date=short", "--", "каталог_повний.xml.gz"],
                     capture_output=True, text=True).stdout.strip().splitlines()
print("комітів каталогу: %d (у неглибокому клоні — неповно) · перший: %s" % (len(лог), лог[-1] if лог else "—"))
print("складальник у репозиторії: %s" % ("нема (так каже влиття_в_каталог.py)" if "якого в репозиторії НЕМА" in
      open(os.path.join(К, "zhnyvarka", "влиття_в_каталог.py"), encoding="utf-8").read() else "див. влиття_в_каталог.py"))
