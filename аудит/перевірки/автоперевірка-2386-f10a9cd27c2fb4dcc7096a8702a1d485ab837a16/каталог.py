"""Звіряє весь каталог, чергу й збережені стани з призначеною головою."""
import collections, csv, gzip, json, re, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

дерево = Path(sys.argv[1]).resolve()
тимчасова = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(дерево/'zhnyvarka'))
sys.path.insert(0, str(дерево/'джерела'))
import складальник as с
import чистка_каталогу as ч
import кадри_маніфест
from жнива_каталог import адреса

база = subprocess.check_output(['git', 'merge-base', '8c0361434e0a3f3934f45fb54a8c2d315a31aadb', 'f10a9cd27c2fb4dcc7096a8702a1d485ab837a16'], cwd=дерево, text=True).strip()
def розпакувати(дані):
    return [json.loads(р) for р in gzip.decompress(дані).splitlines()]
старі = розпакувати(subprocess.check_output(['git', 'show', база+':каталог_записи_v1.jsonl.gz'], cwd=дерево))[1:]
шапка, *нові = розпакувати((дерево/'каталог_записи_v1.jsonl.gz').read_bytes())
def параметри(р):
    return {п[0]:п[1] for п in р['параметри']}
def є_склад(р):
    п = параметри(р)
    return bool(п.get('Склад') or п.get('склад'))
print('БАЗА:', база)
for назва, записи in [('ДО', старі), ('ПІСЛЯ', нові)]:
    урли = collections.Counter(адреса(р['адреса']) for р in записи)
    print(назва, json.dumps(dict(записів=len(записи), повторів=sum(v-1 for v in урли.values()), склад=sum(map(є_склад, записи)), theoriginals=sum('theoriginals.com.ua' in р['адреса'] for р in записи), фото25union_хибні=sum(any(re.search(r'/katalog/.*/image/cache/', к) for к in р.get('кадри', [])) for р in записи), описи=sum(bool(р.get('опис')) for р in записи)), ensure_ascii=False))
нові_за_ід = {р['ід']:р for р in нові}
print('Втрачено нормалізованих адрес:', len({адреса(р['адреса']) for р in старі}-{адреса(р['адреса']) for р in нові}))
print('Стерто старих складів:', sum(є_склад(р) and not є_склад(нові_за_ід[р['ід']]) for р in старі if р['ід'] in нові_за_ід))
print('Стерто старих описів:', sum(bool(р.get('опис')) and not нові_за_ід[р['ід']].get('опис') for р in старі if р['ід'] in нові_за_ід))
нема_старої = [р for р in нові if р.get('ціна_стара') and not р.get('стара_ціна')]
різні_старі = [р for р in нові if р.get('ціна_стара') and р.get('стара_ціна') and float(р['ціна_стара']) != float(р['стара_ціна'])]
print('Стара ціна є, oldprice відсутній:', len(нема_старої), '; oldprice застарів:', len(різні_старі))
for р in нема_старої[:1]+різні_старі[:1]:
    print('ЦІНА:', json.dumps({к:р.get(к) for к in ['ід','адреса','ціна','ціна_стара','стара_ціна']}, ensure_ascii=False), 'XML oldprice:', ET.fromstring(с.офер_xml(р)).findtext('oldprice'))
xml = gzip.decompress((дерево/'каталог_повний.xml.gz').read_bytes()).decode('utf-8')
print('XML дорівнює v1 з маніфестом:', с.скласти(шапка, нові, кадри_маніфест.читати()) == xml)
for назва, сире in [('база', gzip.decompress(subprocess.check_output(['git','show',база+':каталог_повний.xml.gz'], cwd=дерево))), ('голова', xml.encode())]:
    файл = тимчасова/f'{назва}-чистка.xml'; файл.write_bytes(сире)
    try:
        ч.забезпечити_чистим(_шлях=str(файл))
        print('Перша чистка', назва, ': успішна; оферів', len(ET.parse(файл).findall('.//offer')))
        print('Двійників після першої чистки', назва, ':', len(ч.всі_двійники(ET.parse(файл).getroot())))
    except SystemExit as п:
        print('Перша чистка', назва, ': відмовила, код', п.code)
рег = list(csv.DictReader((р for р in (дерево/'zhnyvarka/магазини.tsv').read_text(encoding='utf-8').splitlines() if not р.startswith('#')), delimiter='\t'))
увімкнено = {р['домен'] for р in рег if р['стан']=='увімкнено'}
стани = list(csv.DictReader((дерево/'аудит/жнива_5_3/повний-обхід_стан.tsv').open(encoding='utf-8'), delimiter='\t'))
стани = [р for р in стани if р['домен'] in увімкнено]
print('Увімкнено:', len(увімкнено), '; станів:', len(стани), '; адрес:', sum(int(р['адрес']) for р in стани), '; готово:', sum(int(р['готово']) for р in стани), '; залишок (включно з ознаками невідомого хвоста):', sum(int(р['лишилось']) for р in стани))
print('Незавершених без причини:', sum(bool(int(р['лишилось'])) and not р['причина_код'] for р in стани))
for р in стани:
    if р['домен'] in ('feelyou.com.ua', 'honchstudio.com', 'likeangel.com.ua'):
        print('СТАН:', json.dumps(р, ensure_ascii=False))
with gzip.open(дерево/'аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz', 'rt', encoding='utf-8') as ф:
    черга = list(csv.DictReader(ф, delimiter='\t'))
print('Черга рядків:', len(черга), '; стовпці:', list(черга[0]))
print('Приклад черги:', json.dumps(черга[0], ensure_ascii=False))
хибні = [р for р in черга if re.search(r'https?://25union\.com\.ua/katalog/[^\t\n]*?/image/cache/', json.dumps(р, ensure_ascii=False))]
print('Хибних адрес 25union у черзі:', len(хибні))
for р in хибні[:1]:
    print('ХИБНА ЧЕРГА:', json.dumps(р, ensure_ascii=False))
