import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
from curl_cffi import requests

sha = '506b21f4b061658edb880431d12c150bb7199563'
out = Path('../tmp/кадри4080').resolve()
out.mkdir(exist_ok=True)
def show(path):
    return subprocess.check_output(['git', 'show', f'{sha}:{path}'])
folder = 'аудит/проби/кадр_варіант_кв1_очима_1511/'
rows = list(csv.DictReader(io.StringIO(show(folder+'кадри.tsv').decode('utf-8')), delimiter='\t'))[-10:]
sample = {r['ід']: r for r in csv.DictReader(io.StringIO(show(folder+'вибірка.tsv').decode('utf-8')), delimiter='\t')}
ca = 'C:/Users/gemini/gemini-data/кадр_варіант_кв1_канал_1411/системні_CA/довірені_CA.pem'
(out.parent/'ca.pem').write_bytes(Path(ca).read_bytes())
ca = str(out.parent/'ca.pem')
def get(pair):
    n, row = pair
    r = requests.get(row['адреса_кадру'], verify=ca, timeout=60, impersonate='chrome')
    r.raise_for_status()
    p = out / f'{n:02}.img'
    p.write_bytes(r.content)
    digest = hashlib.sha256(r.content).hexdigest()
    return dict(номер=n, ід=row['ід'], адреса=row['адреса_кадру'], код=r.status_code,
                sha256=digest, збіг_sha256=digest==row['sha256'], файл=str(p),
                сторінка=sample[row['ід']], content_type=r.headers.get('content-type'))
with ThreadPoolExecutor(max_workers=4) as pool:
    result = list(pool.map(get, enumerate(rows, 1)))
(out/'кадри.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
sheet = Image.new('RGB', (1800, 1040), 'white')
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 19)
for n, r in enumerate(result):
    im = Image.open(r['файл']).convert('RGB')
    im.thumbnail((350, 470))
    x, y = (n%5)*360, (n//5)*520
    sheet.paste(im, (x+(360-im.width)//2,y+32))
    ImageDraw.Draw(sheet).text((x+5,y+5), f"{n+1}. №{rows[n]['номер']} {rows[n]['крамниця']}", fill='black', font=font)
sheet.save(out/'нові-кадри.jpg', quality=90)
print(json.dumps(result, ensure_ascii=False, indent=1))
