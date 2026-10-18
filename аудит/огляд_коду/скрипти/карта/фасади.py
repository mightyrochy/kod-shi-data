import json,sys,os
g=json.load(open(sys.argv[1])); Е=g['ребра']; В=g['внутр']; Я=set(g['ядро'])
os.chdir(sys.argv[2])
Ф={'accessory':'аксесуари_','feed':'фід_','суд_образу':'суд_','palette':'палітра_','silhouette':'силует_','composer':'композитор_','bridge':'міст_','outer':'верхнє_'}
for ф,п in Ф.items():
  тіла=[м for м in Я if м.startswith(п) and м!=ф]
  рф=sum(1 for _ in open(ф+'.py')); рт=sum(sum(1 for _ in open(м+'.py')) for м in тіла)
  ф_тягне=[м for м in тіла if м in Е[ф]]
  тіла_тягнуть_фасад=[м for м in тіла if ф in Е[м]]
  чужі_в_тіла=sorted({(з,м) for з in Я for м in тіла if м in Е[з] and з!=ф and not з.startswith(п)})
  чужі_в_фасад=[з for з in Я if ф in Е[з] and not з.startswith(п)]
  тіла_в_тіла=sum(1 for а in тіла for б in тіла if б in Е[а])
  print(f"{ф}: фасад {рф} р., тіл {len(тіла)} ({рт} р.); фасад імпортує тіл {len(ф_тягне)}; тіл, що імпортують фасад {len(тіла_тягнуть_фасад)} (у функціях {sum(1 for м in тіла_тягнуть_фасад if ф in В[м])}); чужих модулів -> фасад {len(чужі_в_фасад)}; чужих ребер -> тіла напряму {len(чужі_в_тіла)} від {len({з for з,_ in чужі_в_тіла})} модулів; тіло->тіло {тіла_в_тіла}")
  print('   напряму в тіла:', ', '.join(sorted({з for з,_ in чужі_в_тіла}))[:300])
