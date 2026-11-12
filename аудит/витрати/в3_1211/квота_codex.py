"""Codex: витрачені в.п. тижневої квоти 10080MIN — сума спадів медіан годин (як В.3 минулого тижня), скидання — зростання."""
import csv,os,statistics,collections
В=os.path.dirname(os.path.abspath(__file__))+'/../токени_ноутбука_1211/'
г=collections.defaultdict(list)
for r in csv.DictReader(open(В+'квота.csv')):
    if r['вікно']=='10080MIN' and r['група']=='codex': г[r['час_UTC'][:13]].append(float(r['залишок_відсотків']))
год=sorted(г); м=[(h,statistics.median(г[h])) for h in год]
спад=0; зрост=[]
for (h0,a),(h1,b) in zip(м,м[1:]):
    if b<a: спад+=a-b
    elif b>a: зрост.append((h1,a,b))
print('годин із зчитуваннями',len(год),'з 168; перша',м[0],'остання',м[-1])
print('витрачено в.п. (сума спадів)',round(спад,1)); print('зростань залишку',len(зрост),зрост)
