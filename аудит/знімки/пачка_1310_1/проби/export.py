from pathlib import Path
import gzip,hashlib,json,shutil,subprocess
src=Path('/tmp/pachka-1310-evidence')
dst=Path('/tmp/liusterko-pachka-1310-media7/аудит/знімки/пачка_1310_1');dst.mkdir(parents=True,exist_ok=True)
assert 'Повна батарея ОДИН раз' in (src/'батарея-загальний.log').read_text()
assert all(x['код']==0 for x in json.loads((src/'батарея/результати.json').read_text()))
def save(s,p,compressed=False):
    p=dst/p;p.parent.mkdir(parents=True,exist_ok=True)
    data=s.read_bytes();p.write_bytes(gzip.compress(data,mtime=0) if compressed else data)
for p in src.glob('*.log'):save(p,Path('логи')/(p.name+'.gz'),True)
save(src/'композиція.json',Path('композиція.json'))
save(src/'доповнення-workflow89.json',Path('доповнення-workflow89.json'))
save(src/'jobs0.json',Path('jobs0.json'))
save(src/'source-PNG-порівняння.json',Path('source-PNG-порівняння.json'))
save(src/'досяжність-звіт.md',Path('досяжність-звіт.md.gz'),True)
save(src/'батарея/результати.json',Path('батарея/результати.json'))
for p in (src/'батарея').glob('*.log'):save(p,Path('батарея')/(p.name+'.gz'),True)
save(src/'інвентар-replay.json',Path('інвентар-replay.json.gz'),True)
for folder,target in [('.qa4941/after','4941'),('.qa5080/after','5080'),('native5070','native5070')]:
    for p in (src/folder).iterdir():
        if p.suffix=='.png':save(p,Path(target)/p.name)
        elif p.suffix=='.json':save(p,Path(target)/(p.name+'.gz'),True)
save(src/'.qa5080/fixture.json',Path('5080/fixture.json.gz'),True)
for name in ['composition.py','battery.py','native5070.js','ui5080.js','ui4941.js','workflow89.py','export.py']:
    p=Path('/tmp/pachka-1310-'+name);save(p,Path('проби')/name)
metadata={'голова_пачки':'09ff6b7b5a46327666d633e1ba798f249941bb4d','main':'8f22756364e060d4fc968671be11740d6aed8ceb','PR':985,'source_PR':[978,979,980,981,982,983],'браузер':'Chromium 151.0.7922.173','Pyodide':'0.26.4','екран':'390×844','повна_збірка':{'sha256':hashlib.sha256((src/'index.html').read_bytes()).hexdigest(),'байти':(src/'index.html').stat().st_size,'модулі':155,'каталог':11993},'постійна_проба5030':{'каталог':11887,'вад':0,'neutral_family_changes':9118,'темні_бурі':486,'кольорові_контролі':2283},'інвентар':'replay побайтово рівний committed source981; сирих offer12426, знаменник1384, явних links0','native5030':'справжній producer→повний/компактний пакет: unknown і known #808080, 4/4','native5070':'7 станів; зростові native JSON побайтово рівні frozen main ДО, невідомі мірки чесні, обов’язкові шляхи відхилено','JS5080':'кожна з2 плиток tap/Enter правильна,4/4; pagerBoth/storage/return/freshRender збережено','JS4941':'7 сцен;6CTA trusted touch/focus/scroll0, PNG390×844','межі':'архівні/синтетичні записи; без живих моделей, API, фото-вимірів; знімки силуетів не є оцінкою фото; ця підготовка не є незалежним прийняттям','нові_медіа_main':0,'attach_artifact':'відсутній у актуальному ALL_TOOLS, успішного прикріплення не заявлено'}
(dst/'факти.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
manifest={str(p.relative_to(dst)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dst.rglob('*')) if p.is_file() and p.name!='SHA256.json'}
(dst/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Файлів доказів',len(manifest),'PNG',sum(k.endswith('.png') for k in manifest),'SHA256 збережено')
