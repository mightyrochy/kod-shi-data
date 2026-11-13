import sys, pathlib, json, os, hashlib, collections
source=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(source))
import feed as Ф, fit as П, silhouette as С, hypergraph as Г, accessory as А, дріт_моделі as Д
catalog=pathlib.Path(sys.argv[2])
root=pathlib.Path(sys.argv[3])
items,_=Ф.читати_yml(str(catalog))
belts=[]
for o in items:
    r=Ф.побудувати_запис_речі(o)
    if r['слот']=='пояс': belts.append(dict(r,назва=o.get('назва'),id=o.get('id')))
result={'джерела':str(source),'каталог_sha256':hashlib.sha256(catalog.read_bytes()).hexdigest(),'оферів':len(items),'поясів':len(belts),'жінки':[]}
for n in (8,7,6,4):
    m=json.loads((root/'аудит/проби/жінки'/f'ж{n}.json').read_text(encoding='utf8'))['мірки']; h=m.pop('зріст'); t=П.тіло(h,m)
    z=П.зони(t); e=next(e for e in Г.ребра(t) if e['ід']=='якір_обʼєму')
    counts=collections.Counter()
    for belt in belts:
        f=А.передумови_пояса(t,[belt])
        counts[str([(x['сила'],x['сила_нп']) for x in f])]+=1
    wire=Д.людина({'тіло':dict(ярлик=z['ярлик'],зони=z['вектор'])})['body']
    result['жінки'].append({'жінка':n,'маршрут':z['ярлик'],'талія':z['вектор']['талія_виражена'],'роль':С.ролі_зон(t)['ролі']['талія'],'якір':e['напруга'],'дріт':wire,'пояси':dict(counts)})
print(json.dumps(result,ensure_ascii=False,indent=2))
