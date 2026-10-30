import gzip,hashlib,json,pathlib,subprocess,sys,xml.etree.ElementTree as ET
root=pathlib.Path(__file__).parent/'pr2386'
out=pathlib.Path(__file__).parent/'evidence2386'
sys.path.insert(0,str(root/'джерела'))
import чистка_каталогу as clean
target=out/'catalog-clean.xml'
target.write_bytes(gzip.decompress((root/'каталог_повний.xml.gz').read_bytes()))
count=lambda:sum(1 for _ in ET.parse(target).iter('offer'))
print('Оферів ДО:',count(),flush=True)
result=clean.забезпечити_чистим(_шлях=str(target))
print('Штатна підготовка фіда: код 0; почищено:',result['почищено'],'оферів ПІСЛЯ:',count(),flush=True)
print('Брудність ПІСЛЯ (екранування, двійники, назви):',clean._брудність(str(target)),flush=True)
digest=hashlib.sha256(target.read_bytes()).hexdigest()
clean.почистити(str(target),str(target))
print('Друга чистка не змінює байти:',digest==hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
cmd=[sys.executable,'проби/жниварка_мовні_5656.py',str(root/'каталог_повний.xml.gz'),str(target)]
print('Команда:', ' '.join(cmd),flush=True)
r=subprocess.run(cmd,cwd=root/'джерела')
print('Код:',r.returncode,flush=True)
sys.exit(r.returncode)
