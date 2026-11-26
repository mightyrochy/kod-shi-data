import json,sys,re
D=sys.argv[1]; s=json.load(open(D+'/стан.json'))
об=[json.loads(l) for l in open(D+'/обміни.jsonl')]
ядр=[o for o in об if o['тип']=='інший промпт']
к1=[к for к in s['картки'] if к and str(к['рука'])=='1'][0]
картка=sorted((float(р['ціна']),р['слот']) for р in к1['речі']); print('картка', к1['ядро']['образ'], к1['ядро']['вирок'], картка)
скл=None; вибір=None
for o in ядр:
  try: в=json.loads(o['відповідь'])
  except Exception: continue
  if 'outfits' in в: скл=(o,в)
  if 'chosen' in в: вибір=в['chosen']
print('вибір моделі', вибір)
o,в=скл
t=json.dumps(o["запит"],ensure_ascii=False).replace(chr(92)+chr(34),chr(34))
for of in в['outfits']:
  if of['id']==к1['ядро']['образ']:
    рядки=[]
    for n in of['items']:
      m=re.search(r'\["'+re.escape(n)+r'",([0-9.]+),"([^"]+)"', t); рядки.append((n, float(m.group(1)), m.group(2)) if m else (n,None,None))
    print('образ', of['id'], рядки)
    print('ціни збіг', sorted(р[1] for р in рядки)==[c for c,_ in картка])
