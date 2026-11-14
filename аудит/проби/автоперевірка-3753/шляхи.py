"""Фактичні шляхи #3753. Запуск: python -X utf8 <цей файл> <дерево PR> [<зібраний html>]."""
import base64
import gzip
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import zipfile

дерево = Path(sys.argv[1]).resolve()
дж = дерево / "джерела"
if len(sys.argv) == 2:
    os.chdir(дж)
    sys.path.insert(0, str(дж))
    import таблиця_каталогу as Т
    оригінал = Т.база_кроками
    def записати(*а, **к):
        результат = yield from оригінал(*а, **к)
        print("Реальна проба сід3_солі дійшла до читача таблиці:", json.dumps(dict(
            дозвіл=os.environ.get("ТАБЛИЦЯ_ПОВІЛЬНИЙ"), результат=результат, стан=Т.СТАН), ensure_ascii=False))
        # Межа виміру: факт переходу на повільну побудову вже встановлено; саму побудову не міряємо.
        raise SystemExit(76)
    Т.база_кроками = записати
    try:
        runpy.run_path("проби/сід3_солі.py", run_name="__main__")
    except SystemExit as е:
        if е.code != 76:
            raise
        print("Перехоплення завершено перед повільною побудовою; це не повний прогін проби.")
else:
    сторінка = Path(sys.argv[2]).resolve().read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="таблиця_перевірка_") as тим:
        модулі = Path(тим)
        б64 = re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"', сторінка).group(1)
        zipfile.ZipFile(io.BytesIO(base64.b64decode(б64))).extractall(модулі)
        sys.path.insert(0, str(дж / "прилади"))
        import сторож_таблиці as С
        таблиця = модулі / С.ТАБЛИЦЯ
        т = json.loads(gzip.decompress(таблиця.read_bytes()))
        фід = модулі / т["фід_ім"]
        if not фід.exists() and (модулі / "каталог_brief.xml").exists():
            фід = модулі / "каталог_brief.xml"  # у вантажі збирач використовує спільне ім'я
        if not фід.exists() and Path(str(фід) + ".gz").exists():
            фід.write_bytes(gzip.decompress(Path(str(фід) + ".gz").read_bytes()))
        інший = модулі / "інший.xml"
        інший.write_text(re.sub(r"<name>.*?</name>", "<name>Інший фід перевірки</name>",
                                фід.read_text(encoding="utf-8"), count=1, flags=re.S), encoding="utf-8")
        print("Сторож до запуску з іншим фідом:", С.вимагати(str(модулі), таблиця=str(таблиця)), flush=True)
        sys.path.insert(0, str(модулі))
        import таблиця_каталогу as Т
        print("Штатний читач на тому самому фіді:", Т._розбіжність(т, str(інший), str(модулі), 0,
              str(модулі / "порожній_кеш.json")), flush=True)
        команда = [sys.executable, "-X", "utf8", str(дж / "проби/намір_каталог_27.py"),
                   str(модулі), str(таблиця), str(інший)]
        р = subprocess.run(команда, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        print("КОМАНДА:", json.dumps(команда, ensure_ascii=False))
        print("КОД:", р.returncode)
        print(р.stdout)
        print(р.stderr)
