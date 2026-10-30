"""Звіряє зміну останньої доробки, лічби черги й збереженої вибірки 5.1."""
import collections, csv, gzip, json, re, subprocess, sys, urllib.request
from pathlib import Path
sys.stdout = open(sys.argv[1], 'w', encoding='utf-8', buffering=1)
def записи(дані):
    return [json.loads(р) for р in gzip.decompress(дані).splitlines()][1:]
до = записи(subprocess.check_output(['git','show','05ec25ea28e5d3dc1a23dc20ffae84c8ce507034:каталог_записи_v1.jsonl.gz']))
після = записи(Path('каталог_записи_v1.jsonl.gz').read_bytes())
за_ід = {р['ід']:р for р in після}
хибні = [р for р in до if any(re.search(r'/katalog/.*/image/cache/',к) for к in р.get('кадри',[]))]
print('Фото з /katalog/.../image/cache ДО останньої доробки:',len(хибні),'ПІСЛЯ:',sum(any(re.search(r'/katalog/.*/image/cache/',к) for к in р.get('кадри',[])) for р in після))
for і in range(0,len(хибні),max(1,len(хибні)//12)):
    if і >= (len(хибні)//12)*12:
        break
    р = за_ід[хибні[і]['ід']]
    url = р['кадри'][0]
    try:
        with urllib.request.urlopen(url,timeout=30) as ф: print('HTTP фото:',р['ід'],ф.status,ф.headers.get('Content-Type'),url)
    except Exception as п: print('HTTP фото:',р['ід'],type(п).__name__,str(п),url)
with gzip.open('аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz','rt',encoding='utf-8') as ф:
    черга = list(csv.DictReader(ф,delimiter='\t'))
print('Черга речей:',len(черга),'кадрів:',sum(int(р['кадрів']) for р in черга))
причини = collections.Counter()
for р in черга:
    for к, ч in re.findall(r'(\w+)=(\d+)',р['причини']): причини[к]+=int(ч)
print('Причини кадрів:',dict(причини))
дані = json.loads(Path('аудит/жнива_5_3/поля_свіжі_усі.json').read_text(encoding='utf-8'))
print('Вибірка 5.1: крамниць:',len(дані['крамниці']))
for назва in ('ДО','ПІСЛЯ'):
    сума = collections.Counter()
    for крамниця in дані['крамниці'].values(): сума.update(крамниця[назва])
    print('5.1',назва,json.dumps(dict(сума),ensure_ascii=False),'дорівнює зведенню:',dict(сума)==дані['разом'][назва])
