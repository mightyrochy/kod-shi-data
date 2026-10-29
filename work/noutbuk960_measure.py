import sys, json, time, pathlib, hashlib, shutil
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'джерела'))
import feed as F
import жнива_кадри as J
from фід_фото import _спільні_фото, _хости_крамниць
out = root / 'аудит' / 'ноутбук_960'
out.mkdir(parents=True, exist_ok=True)
offers = F.читати_yml(F.каталог_на_диску())[0]
enrich = F.читати_збагачення()
shared, hosts = _спільні_фото(offers), _хости_крамниць(offers)
J._прочитати_індекс()
for oid in ['ж-03995@maxa.ua', 'ж-01706@ricamare.com.ua', 'ж-05085@brenda.ua']:
    matches = [o for o in offers if o['id'] == oid or o['id'].split('@')[0] == oid.split('@')[0]]
    if len(matches) != 1:
        print(oid, 'matches', len(matches), flush=True)
        continue
    o = matches[0]
    started = time.monotonic()
    rows = J.виміряти_річ(o, enrich.get(o['id']) or {}, shared, hosts, 12, False, 4, None, кеш=True)
    for row in rows:
        key = hashlib.md5(row['url'].encode()).hexdigest()
        cached = J._індекс.get(key) or {}
        if cached.get('шлях'):
            photo = out / (key + '.jpg')
            shutil.copy2(cached['шлях'], photo)
            row['local_photo'] = photo.name
    result = dict(id=o['id'], seconds=time.monotonic()-started, records=rows,
                  product_update=False, visual_acceptance=False)
    (out / (oid.split('@')[0] + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    J.записати_індекс()
    print(o['id'], len(rows), 'frames', result['seconds'], flush=True)
