import sys, json, gzip
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from collections import Counter
sys.path.insert(0, 'zhnyvarka')
for p in Path('джерела/прилади/річ_запис_дані').glob('*.whl'): sys.path.insert(0, str(p))
import жниварка as j
p=Path('аудит/проби/річ_запис_каталог_2026_10_30')
rows=json.loads((p/'вибірка_п3.json').read_text(encoding='utf8'))
c=Counter()
def canon(u, base):
 x=urlsplit(urljoin(base, str(u))); return (x.netloc.lower().removeprefix('www.'), unquote(x.path).rstrip('/'))
for row in rows:
 html=gzip.decompress((p/row['файл']).read_bytes()).decode('utf8',errors='replace')
 soup=j.BeautifulSoup(html,j.ПАРСЕР_HTML); h=soup.find('h1'); block,_=j.вузол_товару(soup,h,j.рецепт_селекторів(row['крамниця']))
 name=j._текст(h,200).strip().casefold() if h and block is not None else ''
 prods=[v for v in j.json_ld(html) if any(t in ('Product','ProductModel','ProductGroup') for t in j._тип_ld(v)) and not v.get('_у_списку')]
 good=[]
 for v in prods:
  u=v.get('url'); u=u if isinstance(u,str) else ''
  n=v.get('name'); n=n.strip().casefold() if isinstance(n,str) else ''
  if (u and canon(u,row['url'])==canon(row['url'],row['url'])) or (name and n==name): good.append(v)
 c['сторінок']+=1; c['блок+h1']+=bool(name); c['product']+=bool(prods); c['один_збіг']+=len(good)==1; c['кілька_збігів']+=len(good)>1; c['без_збігу']+=not good
print(dict(c))
