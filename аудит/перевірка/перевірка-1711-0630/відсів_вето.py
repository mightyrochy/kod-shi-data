import os, sys, pickle, warnings; warnings.simplefilter("ignore")
ДЖ=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела"); sys.path.insert(0, ДЖ); os.chdir(ДЖ)
import каблук as КБ, profile as ПР
каталог, _ = pickle.load(open("/tmp/кеш_п.pkl","rb"))
П=[]
for r in каталог:
    if r.get("слот")!="взуття": continue
    кб=КБ.каблук(r.get("назва"),None,r.get("url")); П.append(dict(r, каблук_є=кб["є"]))
запис_є=lambda r: r.get("каблук") is True or (r.get("каблук_см") or 0)>0
лиш,геть,_=КБ.відсів(П,"нема",поле=None)
print("пар", len(П), "після відсів «нема»: лишилось", len(лиш), "з каблуком за записом", sum(map(запис_є,лиш)))
після_вето=[r for r in лиш if not ПР.вето_збіг("підбори", r)]
print("після вето пулу «підбори» (profile.вето_збіг): лишилось", len(після_вето), "з каблуком за записом", sum(map(запис_є,після_вето)))
print("джерело «нема»: вето «підбори» →", КБ.прохання_з_паспорта({"перекладено_шаром":True,"вето":{"типи":["підбори"]}}))
