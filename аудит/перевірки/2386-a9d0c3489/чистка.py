"""Повторює першу штатну чистку на незалежних XML бази й призначеної голови."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf8")
корінь = Path.cwd()
sys.path.insert(0, str(корінь / "джерела"))
import чистка_каталогу as ч

вихід = корінь.parent / "evidence2386-current"
вихід.mkdir(exist_ok=True)
for назва, sha in (("ДО", "560fa388e75fe10abe27145644d12d1be2266ab5"),
                   ("ПІСЛЯ", "a9d0c34898ac51ec8ea349b10b69ce9666c2210f")):
    файл = вихід / (назва + ".xml")
    файл.write_bytes(gzip.decompress(subprocess.check_output(["git", "show", sha + ":каталог_повний.xml.gz"])))
    ч.почистити(str(файл), str(файл))
    двійники = ч.всі_двійники(ET.parse(файл).getroot())
    print(назва, "двійників після першої штатної чистки:", len(двійники))
    for пара in двійники:
        print(json.dumps([dict(ід=x.get("id"), адреса=x.findtext("url"), назва=x.findtext("name"))
                          for x in пара[:2]], ensure_ascii=False))
