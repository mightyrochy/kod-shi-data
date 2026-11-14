"""Повторна перевірка #3753: фактичний шлях проби або чужий фід. Аргументи: <дерево PR> <проба.py|фід>."""
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
if sys.argv[2] != "фід":
    os.chdir(дж)
    sys.path.insert(0, str(дж))
    import таблиця_каталогу as Т
    оригінал = Т.база_кроками

    def записати(*а, **к):
        результат = yield from оригінал(*а, **к)
        print("Читач таблиці:", json.dumps(dict(
            проба=sys.argv[2], дозвіл=os.environ.get("ТАБЛИЦЯ_ПОВІЛЬНИЙ"),
            результат=результат, стан=Т.СТАН), ensure_ascii=False))
        raise SystemExit(76)

    Т.база_кроками = записати
    try:
        runpy.run_path("проби/" + sys.argv[2], run_name="__main__")
    except SystemExit as е:
        if е.code != 76:
            raise
        print("Зупинено перед побудовою: виміряно лише досягнення повільного шляху.")
else:
    сторінка = (дерево / "index.html").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="повтор3753_") as тим:
        модулі = Path(тим)
        б64 = re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"', сторінка).group(1)
        zipfile.ZipFile(io.BytesIO(base64.b64decode(б64))).extractall(модулі)
        sys.path.insert(0, str(дж / "прилади"))
        import сторож_таблиці as С
        таблиця = модулі / С.ТАБЛИЦЯ
        т = json.loads(gzip.decompress(таблиця.read_bytes()))
        фід = модулі / т["фід_ім"]
        if not фід.exists():
            фід = модулі / "каталог_brief.xml"
        if not фід.exists() and Path(str(фід) + ".gz").exists():
            фід.write_bytes(gzip.decompress(Path(str(фід) + ".gz").read_bytes()))
        інший = модулі / "інший.xml"
        інший.write_text(re.sub(r"<name>.*?</name>", "<name>Інший фід перевірки</name>",
                                фід.read_text(encoding="utf-8"), count=1, flags=re.S), encoding="utf-8")
        print("Ключ початкового вантажу:", С.розбіжність(str(модулі), фід=str(фід)), flush=True)
        команда = [sys.executable, "-X", "utf8", str(дж / "проби/намір_каталог_27.py"),
                   str(модулі), str(таблиця), str(інший)]
        р = subprocess.run(команда, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        print("КОМАНДА:", json.dumps(команда, ensure_ascii=False))
        print("КОД:", р.returncode)
        print(р.stdout)
        print(р.stderr)
