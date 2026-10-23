"""Одна сцена й один каталог: основа аргументом, моделі не викликаються."""
import sys,pathlib,json,os,collections
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parents[3]).resolve();sys.path.insert(0,str(root/'джерела'));os.chdir(root/'джерела')
import мовний_шар as м,сценарій as с,feed as ф,bridge as б,вибір_палітри as в
record=json.loads((pathlib.Path(__file__).resolve().parents[3]/'джерела/проби/паспорт_один_опис_8740.json').read_text());prompt={'her_new_message':record['слова']};reply=record['відповідь']
res=м.прийняти_розмову(reply);pas=м.паспорт_з_шару(res['внутрішня'],{},слова_ходу=[prompt['her_new_message']])['паспорт']
print('Палітра',json.dumps(в._випадок({'паспорт':pas,'сценарій':{}})[0],ensure_ascii=False))
yoga={'occasion':'sport','occasion_part':'other','part_of_day':'morning','formality':{'from':3,'to':4},'quotes':{'occasion':'йога','occasion_part':'зранку'}}
pas=м.паспорт_з_шару(yoga,{},слова_ходу=['йога зранку'])['паспорт'];scene=с.з_показу({},pas)[0]
base=json.load(open('стенд_вх.json'));cat=ф.каталог_на_диску('каталог_повний.xml');result=json.loads(б.виклик('запити',json.dumps(dict(base,каталог=cat,сценарій=scene,паспорт=pas,випадок='йога зранку'),ensure_ascii=False)))
print('Паспорт',json.dumps({k:pas.get(k) for k in ('нагода','рух','ошатність','цитати_полів')},ensure_ascii=False))
print('Пул',json.dumps({k:dict(collections.Counter(x.get('тип') for x in values)) for k,values in (result.get('кандидати') or {}).items()},ensure_ascii=False))
print('Помилка',result.get('помилка'))
