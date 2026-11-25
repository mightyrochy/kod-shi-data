import json,re
from pathlib import Path
R=Path('аудит/проби/Живий-через-міст')
def load_dir(scene):
    d=R/'стенд/службове'/scene
    lines=(d/'обміни.jsonl').read_bytes().splitlines()
    exchanges=[]
    for line in lines:
        a=json.loads(line)
        q=json.loads(a['запит'])
        body=None
        for msg in q['messages']:
            blocks=msg['content']
            blocks=blocks if isinstance(blocks,list) else [{'type':'text','text':blocks}]
            for b in blocks:
                if b['type']!='text':continue
                try: body,_=json.JSONDecoder().raw_decode(b['text'].lstrip())
                except ValueError:continue
        if not isinstance(body,dict):body={}
        exchanges.append((a,q,body,line))
    tracefile=next((R/scene).glob('verdykty*.json'))
    hfile=d/'руки.jsonl'
    return d, exchanges, tracefile, json.loads(tracefile.read_text()), hfile, [json.loads(l) for l in hfile.open(encoding='utf-8')]
def answer(a):
    r=json.loads(a['відповідь'])
    for b in r.get('content',[]):
        if b['type']=='text':
            try: return json.JSONDecoder().raw_decode(re.sub(r'^\s*```(?:json)?\s*','',b['text']).lstrip())[0]
            except ValueError: continue
    return {}
def records(scene):
    d,x,f,t,hf,h=load_dir(scene)
    opts=[(e['сід'], tuple(r['ід'] for r in p['дані_речей'])) for e in h if e.get('прохід')==1
          for p in e.get('позиції',[]) if str(p.get('рука'))=='1' and p.get('дані_речей')]
    assert len(set(opts))==1
    seed, final=opts[0]
    for i,(a,q,b,_) in enumerate(x):
        if a.get('прохід')!=1 or 'showcase' not in b or not b.get('verdict'): continue
        look={v['your_outfit']['id']:v['your_outfit']['items'] for v in b['verdict']}
        archive_ids={n for r in look.values() for n in r}
        atlas=[]
        for tv in t['прогони'][0]['вердикти']:
            refs={z['номер']:k for k,z in tv.get('етапи',{}).get('довідник_речей',{}).items() if z.get('номер')}
            if archive_ids <= refs.keys(): atlas.append((tv['рука'],refs))
        repairs=answer(a)
        scores=[]
        for j,(aa,aq,ab,_) in enumerate(x[i+1:],i+1):
            if aa.get('прохід')!=1 or 'remarks_by_code' not in ab:continue
            if not ab.get('verdict'):continue
            pick=answer(aa).get('chosen')
            if pick and any(pick==v['id'] for v in repairs.get('outfits',[])):
                v=next(v for v in repairs['outfits'] if pick==v['id'])
                checked=next((w['your_outfit']['items'] for w in ab['verdict'] if w['your_outfit']['id']==pick),None)
                if checked==v['items']: scores.append((j,pick,sum(1 for n,z in zip(checked,final) if any(refs.get(n)==z for _,refs in atlas)),len(checked),len(final)))
        compatible=[]
        for k,(aa,aq,ab,_) in enumerate(x[:i]):
            if aa.get('прохід')!=1 or 'pool' not in ab:continue
            y=answer(aa)
            by={z['id']:z for z in y.get('outfits',[])}
            if all(z in by and ch==by[z]['items'] for z,ch in look.items()):
                compatible.append(k)
        yield i,atlas,look,compatible,scores,seed
if __name__=='__main__':
    for scene in [x.name for x in R.iterdir() if x.name.startswith(('с3_','с5_','с8_'))]:
        print(scene)
        for i,atlas,look,compatible,scores,seed in records(scene):
            print(i,[(r,len(m)) for r,m in atlas],compatible,scores,seed)
