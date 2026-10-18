import json,sys
from collections import Counter
g=json.load(open(sys.argv[1])); Е=g['ребра']; В=g['внутр']; Я=set(g['ядро'])
Е={м:[x for x in Е[м] if x in Я] for м in Я}
# природна глибина з верхньорівневого DAG
Т={м:[x for x in Е[м] if x not in В[м]] for м in Я}
гл={}
def d(м):
  if м in гл: return гл[м]
  гл[м]=0; гл[м]=1+max([d(x) for x in Т[м]],default=-1); return гл[м]
for м in Я: d(м)
вгору=[(м,x) for м in Я for x in Е[м] if гл[x]>=гл[м]]
print('макс глибина',max(гл.values()),'ребер «вгору/вбік» за природною глибиною',len(вгору),'з них у функціях',sum(1 for м,x in вгору if x in В[м]))
def шар(м):
  if м.startswith('реєстр') or м.endswith('_реєстр') or м in('status','каталог_коди','ід_правил','внутрішня_мова','trace','palettes','правило_руки2','знахідка'): return 1
  if м.startswith(('міст_',)) or м in('bridge','протокол','збирач_промптів','сценарій','паспорт_нагоди','мовний_шар','пакет_моделі','дріт_моделі','розбір_відповідей','руки_без_коду','порядок_запиту','language_gate'): return 5
  if м.startswith('суд_') or м in('verify','оцінка_образу','повнота_образу','аксесуари_суд','верхнє_суд','силует_суд','вердикт_моделі'): return 4
  if м.startswith(('фід_','композитор_','аксесуари_','верхнє_')) or м in('feed','семплер','composer','outfit','pipeline','accessory','outer','різноманітність_пулу','таблиця_каталогу','назва_речі','уважний_вибір','приміряння','заміна_речі','річ_з_фото','заміна_з_фото'): return 3
  return 2
Ш={м:шар(м) for м in Я}
print('шари:',Counter(Ш.values()))
print('шар 2:',' '.join(sorted(м for м in Я if Ш[м]==2)))
c=Counter()
for м in Я:
  for x in Е[м]:
    c['вниз' if Ш[x]<Ш[м] else 'вбік' if Ш[x]==Ш[м] else 'вгору']+=1
print(c)
пари=Counter((Ш[м],Ш[x]) for м in Я for x in Е[м] if Ш[x]>Ш[м])
print('вгору за парами шарів',sorted(пари.items()))
вг=[(м,x) for м in Я for x in Е[м] if Ш[x]>Ш[м]]
print('вгору у функціях',sum(1 for м,x in вг if x in В[м]))
print('приклади вгору до 5 (міст/протокол):',sorted({м for м,x in вг if Ш[x]==5}))
print('найчастіші цілі вгору:',Counter(x for м,x in вг).most_common(10))
json.dump(dict(глибина=гл,шар=Ш),open(sys.argv[1]+'.шари','w'),ensure_ascii=False)
