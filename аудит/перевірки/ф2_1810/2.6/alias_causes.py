import pathlib,json,gzip,re,sys,collections
p=pathlib.Path('/workspace/work/f2-26-evidence');sys.path.insert(0,'джерела');import пакет_моделі as П, порядок_запиту as ПЗ
base=[json.loads(x) for x in pathlib.Path('/workspace/work/baseline-results/main-1.jsonl').read_text().splitlines()][1:];after=[json.loads(x) for x in (p/'after-02.jsonl').read_text().splitlines()][1:];ins=[json.loads(json.loads(x)['вхід']) for x in gzip.open('/workspace/work/baseline02/аудит/проби/знімок_входи_сід3.jsonl.gz','rt')];out={};alias_by_hand={};pools=[]
for hand,key in [('1','кандидати'),('2','кандидати_донора')]:
 maps=[]
 for side,allrows in [('до',base),('після',after)]:
  r=allrows[12]['результат'];cs=r[key];order=r['порядок_рук'][hand];shown=ПЗ.перемішати_слоти(cs,order['сід']);m={};byalias={}
  for sl,items in shown.items():
   aliases=order['слоти'].get(sl,[]);assert len(items)==len(aliases),(side,hand,sl)
   for item,alias in zip(items,aliases):
    assert alias not in m or m[alias]==item['id'],(side,hand,alias)
    m[alias]=item['id'];byalias[alias]=item
  prompt=json.loads(r['B' if hand=='1' else 'C']);wire=prompt['pool'];cols=wire['cols'];seen=set()
  for row in wire['rows']:
   obj=dict(zip(cols,row));alias=obj['n'];assert obj['name']==byalias[alias]['назва'],(side,hand,alias);assert obj['price']==byalias[alias]['ціна'];seen.add(alias)
  assert seen==m.keys(),(side,hand,'wire coverage');maps.append(m)
  pools.append({'рука':hand,'бік':side,'унікальних_SKU':len(set(m.values())),'слоти':{k:len(v) for k,v in cs.items()}})
 old,new=maps;alias_by_hand[hand]=maps;out[hand]=[{'alias':al,'SKU_до':old.get(al),'SKU_після':new.get(al),'новий_alias_старого_SKU':next((k for k,v in new.items() if v==old.get(al)),None)} for al in sorted(old.keys()|new.keys()) if old.get(al)!=new.get(al)]
refs=[]
for n in (18,23,24,27,28,31,33,35,39,42):
 iv=ins[n];hand='2' if iv.get('донор') else '1';old,new=alias_by_hand[hand];als=sorted(set(re.findall(r'#\d+·\d+',str(iv.get('текст_моделі') or ''))));refs.append({'виклик':n,'рука':hand,'alias_у_тексті':len(als),'колишніх_правильних':sum(x in old for x in als),'тепер_відсутніх':sum(x not in new for x in als),'тепер_інший_SKU':sum(x in old and x in new and old[x]!=new[x] for x in als),'тотожних':sum(x in old and old.get(x)==new.get(x) for x in als),'точні_пари':[{'alias':x,'SKU_до':old.get(x),'SKU_після':new.get(x)} for x in als]})
report={'sourcehead':'9aea1afd019298f297697831a14f2a1fffcde794','метод':'Незмінена production ПЗ.перемішати_слоти на rawкандидатах call12 зі сідом порядок_рук; позиції зіставлено з alias. Для кожного alias обох рук/обох боків перевірено незмінність SKU між слотами та точний name+price у фактичному wire pool. Wire coverage100%.','пули':pools,'пари_змінених_alias':{k:len(v) for k,v in out.items()},'модельні_посилання':refs};(p/'snapshot-alias-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(p/'snapshot-alias-map.json.gz').write_bytes(gzip.compress(json.dumps(out,ensure_ascii=False,sort_keys=True).encode(),mtime=0));print(json.dumps({'пули':pools,'змінені_alias':report['пари_змінених_alias'],'виклики':[{k:v for k,v in x.items() if k!='точні_пари'} for x in refs]},ensure_ascii=False))

(p/'snapshot-alias-all.json.gz').write_bytes(gzip.compress(json.dumps(alias_by_hand,ensure_ascii=False,sort_keys=True).encode(),mtime=0))
