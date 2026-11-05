"""Для кожного кореня з приладом — у якому злитті `main` за тиждень змінилось число місць.

Прилад і `база:` — з голови B (як у храповику кореня), дерево — коміт злиття. Бісекція по першобатьківських
комітах `main` між A і B: де f(lo)==f(hi) — змін нема (немонотонні зміни всередині не видно).
"""
import json,os,re,shlex,subprocess,sys,threading,time,csv
from concurrent.futures import ThreadPoolExecutor
import os as _os
В=_os.path.dirname(_os.path.abspath(__file__)); R=_os.path.abspath(_os.path.join(В,'../../..'))
sys.path.insert(0,'/tmp/в3/wt/джерела/прилади')
import храповик_кореня as Х
B_WT='/tmp/в3/wt'  # дерево голови B: git worktree add /tmp/в3/wt <B>
A,B=open(В+'/межі.txt').read().split()
import csv as _c
_пр=[x['sha'] for x in _c.DictReader(open(В+'/злиття.csv')) if int(x['продукт'])][::-1]
коміти=[A]+_пр+([B] if _пр[-1]!=B else [])
корені={}
for імя,текст in Х.паспорти_голови(B_WT).items():
    п,а,б,пом=Х.розібрати_паспорт(текст)
    if п and not пом: корені[імя]=(п,а,б)
ВИБРАНІ=sys.argv[1].split(',')
MEMO='/tmp/в3/корені_memo.json'
memo=json.load(open(MEMO)) if os.path.exists(MEMO) else {}
lock=threading.Lock()
пул=[]
for i in range(4):
    wt=f'/tmp/в3/wtk{i}'
    if not os.path.isdir(wt):
        subprocess.run(['git','-C',R,'worktree','add','-q','--detach','--force',wt,A],check=True)
    пул.append(wt)
вільні=list(пул); cv=threading.Condition()
def оцінити(імя,i):
    key=f'{імя}|{коміти[i]}'
    with lock:
        if key in memo: return memo[key]
    with cv:
        while not вільні: cv.wait()
        wt=вільні.pop()
    try:
        subprocess.run(['git','-C',wt,'checkout','-q','--force','--detach',коміти[i]],check=True)
        subprocess.run(['git','-C',wt,'clean','-fdq'],check=True)
        прилад,аргументи,бази=корені[імя]
        for шлях in [прилад,*бази]:
            if os.path.lexists(os.path.join(B_WT,шлях)): Х.покласти(B_WT,wt,шлях)
        t=time.time(); n,чому=Х.лічити(wt,прилад,аргументи)
        v=[n,чому,round(time.time()-t,1)]
    finally:
        with cv: вільні.append(wt); cv.notify()
    with lock:
        memo[key]=v; json.dump(memo,open(MEMO+'.tmp','w')); os.replace(MEMO+'.tmp',MEMO)
        print(імя,i,коміти[i][:8],v,flush=True)
    return v
def бісекція(імя):
    зміни=[]
    def f(i): return оцінити(імя,i)[0]
    def крок(lo,hi,flo,fhi):
        if flo==fhi: return
        if flo is None or fhi is None:
            if hi-lo==1: зміни.append((hi,flo,fhi)); return
        if hi-lo==1: зміни.append((hi,flo,fhi)); return
        mid=(lo+hi)//2; fm=f(mid)
        крок(lo,mid,flo,fm); крок(mid,hi,fm,fhi)
    flo=f(0); fhi=f(len(коміти)-1)
    крок(0,len(коміти)-1,flo,fhi)
    return імя,flo,fhi,зміни
with ThreadPoolExecutor(4) as ex:
    рез=list(ex.map(бісекція,ВИБРАНІ))
with open(В+'/корені_зміни.csv','a',newline='') as fh:
    w=csv.writer(fh)
    for імя,flo,fhi,зміни in рез:
        for (i,a,b) in зміни: w.writerow([імя,коміти[i],a,b])
        print('ПІДСУМОК',імя,flo,fhi,len(зміни),flush=True)
