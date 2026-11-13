from pathlib import Path
import os,sys,json,time,datetime,hashlib
source=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3]/'джерела'; root=source.parent; sys.path.insert(0,str(source)); os.chdir(source)
import таблиця_збирання as З, таблиця_каталогу as Т
start=time.monotonic(); print('Побудова штатної таблиці для незмінених джерел голови',flush=True)
t=З.зібрати(str(source/'каталог_повний.xml'),str(source))
cache=Path(os.environ['TEMP'])/'table-empty-colors-2841.json'; cache.write_text('{}',encoding='utf8')
reason=Т._розбіжність(t,str(source/'каталог_повний.xml'),str(source),0,str(cache))
assert reason is None,reason
out=source/'каталог_таблиця.json.gz'; stage=source/'каталог_таблиця.json.gz.частина'; Т.записати(t,str(stage)); os.replace(stage,out)
meta={'голова':'c3a658023839a2da34e70420d6c9cb4226b02e16','готово_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'секунд':round(time.monotonic()-start,2),'записів':len(t['записи']),'модулів':len(t['ключ']['код']),'ключ_відповідає_джерелам':reason is None,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'команда':'таблиця_збирання.зібрати(каталог, джерела), без байти_модулів; стандартна перевірка рівності всередині збирача'}
Path(__file__).with_name('таблиця-проб.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(meta,ensure_ascii=False),flush=True)
