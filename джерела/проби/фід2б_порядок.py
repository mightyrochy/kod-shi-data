# -*- coding: utf-8 -*-
"""Рядок 1984 (2, 4): `--записати` з нечитабельним збагаченням не міняє каталог; `_зібрана` не вірить битому файлу."""
import gzip, json, os, shutil, sys, tempfile
Т = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(Т, "zhnyvarka"))
import перезняти_галереї as Г, жниварка as Ж
тека = tempfile.mkdtemp()
кат = os.path.join(тека, "к.xml.gz"); shutil.copy(os.path.join(Т, "каталог_повний.xml.gz"), кат)
хеш = lambda: __import__("hashlib").md5(open(кат, "rb").read()).hexdigest()[:8]
до = хеш()
try:
    Г.main(["--каталог", кат, "--магазин", "brenda.ua", "--стеля", "2", "--записати", "--збагачення", os.path.join(тека, "нема.gz"),
            "--знімки", тека])
except Exception as e:
    print("збагачення нечитабельне → %s; каталог змінено: %s" % (type(e).__name__, до != хеш()))
добрий = os.path.join(тека, "a.json.gz"); биті = os.path.join(тека, "b.json.gz"); збій = os.path.join(тека, "c.json.gz")
with gzip.open(добрий, "wt") as f: json.dump(dict(діаг={"стан": "ок"}, прийняті=[1], відхилені=[]), f)
open(биті, "wb").write(gzip.compress('{"діаг":'.encode())[:20])
with gzip.open(збій, "wt") as f: json.dump(dict(діаг={"стан": "ВИНЯТОК: x"}, прийняті=[], відхилені=[]), f)
print("_зібрана: добрий %s, обірваний %s, ВИНЯТОК %s; стара перевірка «файл існує» — усі три True" % (Ж._зібрана(добрий), Ж._зібрана(биті), Ж._зібрана(збій)))
