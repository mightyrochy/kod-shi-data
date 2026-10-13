exec((__import__('pathlib').Path(__file__).with_name('noutbuk960_measure.py')).read_text(encoding='utf-8').split('for oid in ')[0])
from жнива_фото import фото_зі_сторінки, _сторінка
o = next(o for o in offers if o['id'] == 'ж-01706@ricamare.com.ua')
print(o['id'], o['url'], flush=True)
result = dict(id=o['id'], url=o['url'], records=[], visual_acceptance=False)
try:
    html = _сторінка(o['url'])
    (out / 'ricamare_page.html').write_text(html, encoding='utf-8')
except Exception as e:
    result['page_error'] = str(e)
for photo in фото_зі_сторінки(o, 12, мітка=o['id']):
    row = {k:v for k,v in photo.items() if k != 'шлях'}
    if photo.get('шлях'):
        key = hashlib.md5(photo['url'].encode()).hexdigest()
        dest = out / (key + '.jpg')
        shutil.copy2(photo['шлях'], dest)
        row['local_photo'] = dest.name
        part, clusters, why, source, light = J.виміряти_фото(photo['шлях'], 'верх')
        row.update(mask=source, mask_fraction=part, clusters=clusters, why=why)
    result['records'].append(row)
(out / 'ж-01706.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('frames', len(result['records']), result.get('page_error',''), flush=True)
