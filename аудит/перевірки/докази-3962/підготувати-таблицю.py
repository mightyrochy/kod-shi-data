"""Підготувати штатну таблицю каталогу для наступних проб, без зміни модулів чи ключа перевірки."""
import json
import os
import pathlib
import sys
import time
дж = pathlib.Path(sys.argv[1]).resolve() / "джерела"
os.chdir(дж)
sys.path.insert(0, str(дж))
import feed as Ф
import таблиця_збирання as З
import таблиця_каталогу as Т
поч = time.monotonic()
т = З.зібрати(Ф.каталог_на_диску("каталог_повний.xml"), str(дж))
Т.записати(т, str(дж / Т.ІМ))
print(json.dumps(dict(записів=len(т["записи"]), файл=Т.ІМ, секунд=round(time.monotonic() - поч, 2),
                     звірка="зібрати перевірила рівність відновленої бази побудованій"), ensure_ascii=False))
