"""Число місць кожного кореня продукту на межах відрізків злиттів одного постачальника (В.3 §3).

Злиття з кодом продукту (`злиття.csv`, продукт > 0) іде підряд відрізками одного постачальника; прилад і `база:`
— з голови B (як у храповику кореня), дерево — останнє злиття відрізка. Зміна числа між межами — внесок відрізка
(злиття поза кодом продукту між ними число не змінюють — перевірка: межа B після останнього злиття).
Запуск: git worktree add /tmp/в3/wt <B>; python3 корені_за_відрізками.py → корені_відрізки.csv
"""
import csv,json,os,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
В=os.path.dirname(os.path.abspath(__file__)); R=os.path.abspath(os.path.join(В,'../../..'))
B_WT='/tmp/в3/wt'; sys.path.insert(0,B_WT+'/джерела/прилади')
import храповик_кореня as Х
A,B=open(В+'/межі.txt').read().split()
КОРЕНІ=['Е2-втрата-слова','Е2-вікно','Е2-збій-без-сліду','Е2-межі','Е2-промпти','Е2-смуга-погоди','Е2-текст-жінці',
 'Е2-усе-з-розмови','Е2-частина-дня','Е3-заміна-з-перевіркою','Е3-одна-величина','Е3-поле-без-писача','Е3-сила-правила',
 'Річ-запис-речі','Річ-кадр-варіант','Річ-колір-вимір','Річ-колір-межі','Річ-ознаки-обличчя','Річ-примірка-та-сама-людина']
def група(p):
    if p.startswith('пачка:'): return 'Claude' if set(k.rsplit(' ',1)[0] for k in p[7:].split(', '))=={'Claude'} else 'пачки й обгортка до вікна'
    if p=='обгортка (запуск до вікна)': return 'пачки й обгортка до вікна'
    return p
з=[x for x in csv.DictReader(open(В+'/../злиття_2905.csv')) if int(x['продукт'])][::-1]
відрізки=[]
for x in з:
    g=група(x['постачальник'])
    if відрізки and відрізки[-1][0]==g: відрізки[-1][1].append(x)
    else: відрізки.append([g,[x]])
точки=[('A',A)]+[(f'{i+1}:{g}',xs[-1]['sha']) for i,(g,xs) in enumerate(відрізки)]+[('B',B)]
корені={}
for імя,текст in Х.паспорти_голови(B_WT).items():
    п,а,б,пом=Х.розібрати_паспорт(текст)
    if імя in КОРЕНІ and п and not пом: корені[імя]=(п,а,б)
MEMO='/tmp/в3/корені_memo.json'
memo=json.load(open(MEMO)) if os.path.exists(MEMO) else {}
wt='/tmp/в3/wtk0'
for мітка,sha in точки:
    треба=[і for і in корені if f'{і}|{sha}' not in memo]
    if not треба: continue
    subprocess.run(['git','-C',wt,'checkout','-q','--force','--detach',sha],check=True)
    subprocess.run(['git','-C',wt,'clean','-fdq'],check=True)
    for і in треба:
        п,_,б=корені[і]
        for шлях in [п,*б]:
            if os.path.lexists(os.path.join(B_WT,шлях)): Х.покласти(B_WT,wt,шлях)
    with ThreadPoolExecutor(4) as ex:
        рез=dict(zip(треба,ex.map(lambda і:Х.лічити(wt,корені[і][0],корені[і][1]),треба)))
    for і,(n,чому) in рез.items(): memo[f'{і}|{sha}']=[n,чому,None]
    json.dump(memo,open(MEMO+'.tmp','w')); os.replace(MEMO+'.tmp',MEMO)
    print(мітка,sha[:8],{і:v[0] for і,v in рез.items()},flush=True)
with open(В+'/корені_відрізки.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['корінь','точка','sha','злиттів_у_відрізку','місць','причина_без_числа'])
    for і in корені:
        for мітка,sha in точки:
            n,чому,_=memo.get(f'{і}|{sha}',[None,'не лічено',None])
            k=next((len(xs) for j,(g,xs) in enumerate(відрізки) if мітка.startswith(f'{j+1}:')),'')
            w.writerow([і,мітка,sha,k,'' if n is None else n,(чому or '')[:200]])
print('ГОТОВО',len(точки),'точок')
