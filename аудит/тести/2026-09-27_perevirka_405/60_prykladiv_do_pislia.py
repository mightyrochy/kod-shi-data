# -*- coding: utf-8 -*-
import gzip, os, re, sys, random
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import назва_речі

ШЛЯХ = "/home/user/kod-shi-data/каталог_повний.xml.gz"
сирий = gzip.open(ШЛЯХ, "rt", encoding="utf-8").read()

назви = [м.group(1) for о in re.finditer(r"<offer\b.*?</offer>", сирий, re.S)
         for м in re.finditer(r"<name>([^<]*)</name>", о.group(0))]
пари = [(н, назва_речі.зняти_артикул(н)) for н in назви]
з_кодом = [(а, б) for а, б in пари if а != б]

print("змінених назв разом:", len(з_кодом))

random.seed(27)
випадкові = random.sample(з_кодом, 30)

найбільша_різниця = sorted(з_кодом, key=lambda p: len(p[0]) - len(p[1]), reverse=True)[:30]

print("\n=== 30 ВИПАДКОВИХ (сід 27) ===")
for а, б in випадкові:
    print("%r -> %r" % (а, б))

print("\n=== 30 З НАЙБІЛЬШОЮ РІЗНИЦЕЮ ===")
for а, б in найбільша_різниця:
    print("%r -> %r" % (а, б))

довгі_числа = [б for _, б in пари if re.search(r"\d{4,}", б)]
print("\nназв ПІСЛЯ правки з довгими числами (>=4 цифри поспіль):", len(довгі_числа))
for х in довгі_числа[:40]:
    print("  ", repr(х))
