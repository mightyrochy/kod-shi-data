# -*- coding: utf-8 -*-
"""Рядок 5629 (реєстр 5616, клас Г9): що жниварка кладе в `<picture>` — сира галерея без перевірки. Факт: скільки
знімків на запис за видом запису, рівно 1 і рівно 12 (стеля), перший знімок, спільний для ≥5 записів крамниці
(логотип, банер, меню), той самий знімок двічі в одній галереї різними розмірами, і скільки записів мають позначку
перевірки фото запитом. Дубль розміру міряється кадром (маніфест кадрів і `без_дублів_розміру`), не іменем файла: ім'я
давало хибні збіги (twice, fromus, emmeliedelage — різний вміст під одним іменем). Мережі не треба. Запуск: python3 джерела/проби/каталог_проблеми_г_галерея.py"""
import collections, gzip, os, re, sys                                              # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
без_запиту = lambda u: u if "/_next/image" in u else re.sub(r"\?.*", "", u)   # у `_next/image` знімок — у запиті (?url=)  # noqa: E731
sys.path.insert(0, os.path.join(К, "zhnyvarka"))
import кадри_маніфест as М                                                    # noqa: E402
кадри = М.читати()
зз = []
for о in re.findall(r"<offer\b.*?</offer>", xml, re.S):
    зз.append(("складальник 07.09" if 'name="бал_інформації"' in о else "жниварка 18.09",
               re.search(r'<param name="магазин">([^<]*)<', о).group(1), re.findall(r"<picture>([^<]*)<", о),
               'name="фото_перевірено"' in о))
for в in ("складальник 07.09", "жниварка 18.09"):
    з = [x for x in зз if x[0] == в]; к = collections.Counter(len(x[2]) for x in з)
    print("%-18s записів %5d · без фото %d · рівно 1 фото %5d · рівно 12 %5d · перевірено запитом %d" % (в, len(з), к[0],
          к[1], к[12], sum(1 for x in з if x[3])))
спільні = collections.Counter((м, без_запиту(ф[0])) for _, м, ф, _ in зз if ф)
сміття = [x for x in зз if x[2] and спільні[(x[1], без_запиту(x[2][0]))] >= 5]
print("перший знімок спільний для ≥5 записів крамниці: %d записів (%.1f %%) · %s" % (len(сміття), 100 * len(сміття) / len(зз),
      collections.Counter(x[1] for x in сміття).most_common(5)))
print("  приклади: %s" % sorted({без_запиту(x[2][0])[-45:] for x in сміття})[:3])
двійні = [x for x in зз if len(М.без_дублів_розміру(x[2], кадри)) < len(x[2])]
print("той самий знімок кількома розмірами в одній галереї (за кадром): %d записів · %s" % (len(двійні),
      collections.Counter(x[1] for x in двійні).most_common(4)))
сл = [x for x in зз if any(re.search(r"(arrow|icon|logo|/play\.|placeholder|loader|lazy|cart\.|\.svg)", u, re.I) for u in x[2])]
print("галерея зі службовою картинкою сайту (стрілка, іконка, лого, play, svg, заглушка): %d записів · %s" % (len(сл),
      collections.Counter(x[1] for x in сл).most_common(4)))
