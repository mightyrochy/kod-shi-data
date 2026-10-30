import gzip, os, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
root=Path.cwd(); sys.path.insert(0,str(root/'джерела'))
import чистка_каталогу as ч
path=root.parent/'evidence2386/base.xml'
path.write_bytes(gzip.decompress(subprocess.check_output(['git','show','560fa388e75fe10abe27145644d12d1be2266ab5:каталог_повний.xml.gz'])))
try:
    result=ч.забезпечити_чистим(_шлях=str(path))
    print({k:v for k,v in result.items() if k!='звіт'})
except SystemExit as e:
    print('БАЗА: код',e.code)
