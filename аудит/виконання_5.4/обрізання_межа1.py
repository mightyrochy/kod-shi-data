import os,re,sys,json,statistics as st,collections
sys.path.insert(0,'джерела')
import каталог_розбір_прогін as П
import каталог_розбір as КР
D='C:/Users/Admin/розбір_5.4_каталог'
схема=КР.схема_відповіді()
ключі=list(схема['properties'])
def розбір(відп):
    try: return json.loads(відп),True
    except ValueError: pass
    # відновлення обрізаного префікса
    s=відп.rstrip(); стек=[]; рядок=False; екр=False
    for ч in s:
        if рядок:
            if екр: екр=False
            elif ч==chr(92): екр=True
            elif ч=='"': рядок=False
            continue
        if ч=='"': рядок=True
        elif ч in '{[': стек.append('}' if ч=='{' else ']')
        elif ч in '}]':
            if not стек or стек[-1]!=ч: return None,False
            стек.pop()
    хв=s
    if рядок: хв+='"'
    for _ in range(6):
        for кінець in ('', 'null','0','""'):
            for зам in (хв, re.sub(r'[,:]\s*$','',хв), re.sub(r',?\s*"[^"]*"\s*:?\s*$','',хв), re.sub(r',\s*$','',хв)):
                ст=[];р=False;е=False
                for ч in зам:
                    if р:
                        if е: е=False
                        elif ч==chr(92): е=True
                        elif ч=='"': р=False
                        continue
                    if ч=='"': р=True
                    elif ч in '{[': ст.append('}' if ч=='{' else ']')
                    elif ч in '}]': ст.pop()
                try: return json.loads(зам+кінець+''.join(reversed(ст))),False
                except ValueError: pass
        break
    return None,False
R=[];T=[]
for f in sorted(os.listdir(D)):
    if not f.endswith('.txt'): continue
    дані,відп=П.розділити(open(D+'/'+f,encoding='utf-8').read())
    о,ціла=розбір(відп)
    (R if ціла else T).append((f,дані,відп,о))
print('файлів',len(R)+len(T),'цілих JSON',len(R),'обрізаних/неJSON',len(T))
def квоти(о,шлях=''):
    if isinstance(о,dict):
        for к,в in о.items():
            if к=='quote' and isinstance(в,str): yield шлях,в
            else: yield from квоти(в,шлях+'/'+к)
    elif isinstance(о,list):
        for в in о: yield from квоти(в,шлях)
def стат(набір,мітка):
    повн=[len(в) for f,д,в,о in набір]
    ws=[];кв=[];кв_ні=0;кв_всього=0;довг=collections.defaultdict(list);повтор=0;останній=collections.Counter()
    токени_ц=[];ключі_ок=0;ключ_зайвий=0
    for f,д,в,о in набір:
        зовс=len(re.findall(r'(?<![^\n])[ \t]+',в))
        ws.append(зовс/max(1,len(в)))
        if o:=о:
            if isinstance(о,dict):
                ключі_ок+=all(k in ключі for k in о); останній[list(о)[-1]]+=1
                текст=json.dumps(д,ensure_ascii=False).lower()
                for ш,q in квоти(о):
                    кв.append(len(q)); кв_всього+=1
                    if q and q.lower() not in текст: кв_ні+=1
                for к,зн in о.items():
                    if isinstance(зн,list):
                        довг[к].append(len(зн))
                        сер=[json.dumps(x,sort_keys=True,ensure_ascii=False) for x in зн]
                        повтор+=len(сер)-len(set(сер))
    р=lambda a,q:sorted(a)[min(len(a)-1,int(q*len(a)))] if a else None
    print('\n##',мітка,len(набір))
    print('довжина відповіді, знаків: медіана',st.median(повн),'p90',р(повн,.9),'макс',max(повн))
    print('частка відступів (пробіли після \n) у відповіді: медіана %.2f'%st.median(ws))
    if кв: print('цитати: всього',кв_всього,'медіана',st.median(кв),'p99',р(кв,.99),'макс',max(кв),'· цитат поза текстом речі',кв_ні,'(%.0f%%)'%(100*кв_ні/кв_всього),'· сума знаків цитат на файл (сер.)',round(sum(кв)/len(набір)))
    for к,l in sorted(довг.items()): print('  список',к,'довжина p99',р(l,.99),'макс',max(l),'n',len(l))
    print('повторних пунктів у списках всього',повтор)
    print('ключі лише зі схеми (граматика діяла):',ключі_ок,'з',sum(1 for x in набір if isinstance(x[3],dict)),'· останнє поле в кінці відповіді:',останній.most_common(6))
стат(R,'цілі'); стат(T,'обрізані')
