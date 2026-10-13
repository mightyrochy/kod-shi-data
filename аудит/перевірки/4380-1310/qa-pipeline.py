import os,sys,json,copy,pathlib
root=pathlib.Path('/workspace/scratch/4380-sut-kodamy');out=pathlib.Path('/workspace/scratch/qa4380-r3')
os.chdir(root/'джерела');sys.path.insert(0,str(pathlib.Path.cwd()))
import міст_відповіді as M,pipeline as P,знахідка as Z,аксесуари_розмір as A
fixture=json.loads(pathlib.Path('/workspace/scratch/qa4380-r2/same-name-input.json').read_text())
original=P.перевірити_від_моделі;dedup=Z.без_повторів;produce=A._ворота_однієї
for mode in ('same-name','different-name','same-id-duplicate'):
 cat=copy.deepcopy(fixture['catalog']);v=copy.deepcopy(fixture['input']);stages=[];raw=[];calls=[]
 if mode=='different-name':cat[-1]['назва']='Інші окуляри QA'
 cand={}
 for item in cat:cand.setdefault(item['слот'],[]).append(item)
 M._пакет_каталогу=lambda *a,**kw:dict(готово=True,_каталог=copy.deepcopy(cat),кандидати=copy.deepcopy(cand))
 M._дія_правил=lambda *a,**kw:None
 def capture_producer(*a,**kw):
  r=produce(*a,**kw);raw.append(copy.deepcopy(r));return r
 def capture_dedup(pairs):
  pairs=list(pairs)
  if mode=='same-id-duplicate':
   f=next(((p,z)for p,z in pairs if z.get('правило')=='K-EYE-01' and 'item_frame_size_unreadable' in z.get('суть','')),None)
   if f:pairs.append(('duplicate-bucket',copy.deepcopy(f[1])))
  r=dedup(pairs);stages.append(dict(before=copy.deepcopy(pairs),after=copy.deepcopy(r)));return r
 def capture_pipeline(*a,**kw):
  r=original(*a,**kw);calls.append(copy.deepcopy(r));return r
 A._ворота_однієї=capture_producer;Z.без_повторів=capture_dedup;P.перевірити_від_моделі=capture_pipeline
 owner=json.loads(M.від_моделі(v))
 frames=[q for q in owner['питання'] if q['правило']=='K-EYE-01' and 'item_frame_size_unreadable' in q['суть']]
 assert len(frames)==2 and {q['повідомлення']['statements'][0]['values']['item_id'] for q in frames}=={'qa-frame-17','qa-frame-18'}
 assert len({json.dumps(q['повідомлення'],sort_keys=True)for q in frames})==2
 for q in frames:
  values=q['повідомлення']['statements'][0]['values'];assert values['frame_size']['free_text']=='58-extra-wide' and values['her_pupillary_distance_mm']==64
  assert q['речі']==[next(x['назва']for x in cat if x['id']==values['item_id'])]
 cut=next(q for q in owner['питання']if q['правило']=='K-CUT-00');assert cut['речі']==['qa-top-17'] and cut['повідомлення']['statements'][0]['values']['unknown_cuts'][0]=={'item_id':'qa-top-17','cut':{'free_text':'тестовий невідомий крій','lang':'uk'}}
 zones=[q for q in owner['питання']if q['правило']=='K-BOD-02' and any(s['code']=='fabric_unknown_ease_below_min_if_woven'for s in q['повідомлення']['statements'])]
 assert len(zones)==2 and {s['values']['level'] for q in zones for s in q['повідомлення']['statements']}=={'bust','hips'}
 counts=[]
 for stage in stages:
  f=lambda pairs:[z for p,z in pairs if z.get('правило')=='K-EYE-01'and 'item_frame_size_unreadable'in z.get('суть','')]
  before,after=f(stage['before']),f(stage['after'])
  if before:counts.append([len(before),len(after)]);assert len(after)==2
 (out/(mode+'.json')).write_text(json.dumps(dict(head='ac42f9369a96c4ef6e77e6663e25f3294a330a18',fixture=dict(input=v,catalog=cat),producer=raw,dedups=stages,pipeline=calls,owner=owner),ensure_ascii=False,indent=2))
 print(mode,'raw',len([r for _,r in raw if r and r.get('правило')=='K-EYE-01']), 'dedups',counts,'owner',len(frames),'MODELmessages',len({json.dumps(q['повідомлення'],sort_keys=True)for q in frames}),'bust/hips',len(zones))
