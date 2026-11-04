import gzip, json, hashlib, subprocess, sys, collections
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
r = Path.cwd()
p = r / 'аудит/проби/річ_колір_перезбір_0411'
o = Path(__file__).resolve().parent
o.mkdir(exist_ok=True)
sys.path.insert(0, str(r / 'джерела'))
import фід_кадр_колір as к
читати = lambda n: json.loads(gzip.decompress((p / n).read_bytes()))
д = читати('дельта.json.gz')
б = json.loads(gzip.decompress(subprocess.check_output(['git','show','5b495d55d9972f940e675b14f777fb5079802106:аудит/проби/річ_колір_перезбір_0411/дельта.json.gz'])))
в = {x['id']:x['файли'] for x in json.loads((p/'вибірка.json').read_text(encoding='utf-8'))}
assert set(в) == set(д['записи'])
м = {(x['id'],x['файл'],x['url']):x for x in д['маніфест']}
assert len(м) == len(д['маніфест']) == 188
for x in д['маніфест']:
    assert hashlib.sha256((p/x['фото']).read_bytes()).hexdigest() == x['sha256']
for ід, записи in д['записи'].items():
    assert len(записи) == len(в[ід])
    assert {x['файл'] for x in записи} == set(в[ід])
    assert all((ід,x['файл'],x['url']) in м for x in записи)
for ід, записи in б['записи'].items():
    assert записи == д['записи'][ід]
нові = [(ід,x) for ід, записи in д['записи'].items() if ід not in б['записи'] for x in записи]
assert len(нові) == 41
ш = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for н in range(0,len(нові),10):
    аркуш = Image.new('RGB',(1500,860),'white')
    олівець = ImageDraw.Draw(аркуш)
    for з,(ід,запис) in enumerate(нові[н:н+10]):
        x,y = (з%5)*300,(з//5)*430
        фото = ImageOps.contain(Image.open(p/м[ід,запис['файл'],запис['url']]['фото']).convert('RGB'),(290,300))
        аркуш.paste(фото,(x+(300-фото.width)//2,y))
        вимір = запис.get('вимір') or {}
        for крок, текст in enumerate([f'{н+з+1}: {ід}',запис['файл'][:36],f"{запис.get('маска')} {запис.get('hex')} {вимір.get('візерунок')}",f"придатний: {bool(к.вимір_кадру(запис))} розкид: {запис.get('розкид')}"]):
            олівець.text((x+4,y+303+крок*20),текст,fill='black',font=ш)
        край=x+5
        for _,частка,hex,_ in вимір.get('сегменти',[]):
            праворуч=min(x+295,край+round(частка*290))
            if праворуч>край: олівець.rectangle((край,y+389,праворуч,y+410),fill=hex)
            край=праворуч
    аркуш.save(o/f'кадри-{н//10+1}.jpg',quality=92)
сирий=gzip.decompress((p/'продовження_сирий.log.gz').read_bytes())
дані=dict(галерей=len(д['записи']),кадрів=sum(map(len,д['записи'].values())),фото=len(м),нових_кадрів=len(нові),придатних=sum(bool(к.вимір_кадру(x)) for _,x in нові),сирий_лог_байтів=len(сирий))
print(json.dumps(дані,ensure_ascii=False))
for ід,x in нові:
    вимір = x.get('вимір') or {}
    print(json.dumps(dict(id=ід,файл=x['файл'],фото=м[ід,x['файл'],x['url']]['фото'],тип=x.get('колір_тип'),придатний=bool(к.вимір_кадру(x)),lab=x.get('lab'),hex=x.get('hex'),розкид=x.get('розкид'),візерунок=вимір.get('візерунок'),сегменти=вимір.get('сегменти'),чому=x.get('чому')),ensure_ascii=False))
