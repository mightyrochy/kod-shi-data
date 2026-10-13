import sys,json,hashlib,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import profile as P,bridge as B,pipeline as PL,міст_основи as MO,дріт_моделі as D,пакет_моделі as PM,розбір_відповідей as R
вх=json.load(open('стенд_вх.json')); F,T,зріст,kw=B._збірка(вх)
проф=[]
for в in (None,{}, {'unknown':1}, {'помітність':.5,'непомітність':.5}, {'помітність':.6,'непомітність':.45}, {'помітність':1}, {'непомітність':1}, {'комфорт':1}, {'легкість_збирання':1}, {'доречність':1}):
    проф.append([в,P.мета_з_ваг(в)])
сцени=[]
for м,з,ц,в in ((None,None,None,None),('невідомо',None,None,None),('експресія',None,'  Жінка: “хочу уваги.”\n'+'точна цитата '*20,None),('приховати',['живіт'],'сховати живіт',{'помітність':1}),('приховати',None,'не привертати уваги',None),('вище',None,'вище',None)):
    пак=MO._пакет(F,T,зріст,dict(kw,мета=м,мета_зони=з,мета_слова=ц,ваги_цілей=в))
    л=пак['людина']; др=D.людина(л)
    д=copy.deepcopy(пак); д['людина'].pop('чому_мети',None); д['людина'].pop('цитата_мети',None)
    сцени.append(dict(input=[м,з,ц,в],person=л,wire=др,unaffected=hashlib.sha256(json.dumps(д,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()))
print(json.dumps(dict(profile=проф,cases=сцени,items=[R.перевірити_образ_моделі('',None,перелік=[]) ,R.перевірити_образ_моделі('',None,перелік=json.dumps({'items':[dict(name='Модельна річ',color_hex='#000000',slot='top')]},ensure_ascii=False))]),ensure_ascii=False,indent=2,default=str))
