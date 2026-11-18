import os, sys, pickle, warnings, collections; warnings.simplefilter("ignore")
ДЖ=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела"); sys.path.insert(0, ДЖ); os.chdir(ДЖ)
import каблук as КБ
каталог, _ = pickle.load(open("/tmp/кеш_п.pkl","rb"))
в=[r for r in каталог if r.get("слот")=="взуття"]
є=lambda r: r.get("каблук") is True or (r.get("каблук_см") or 0)>0
вид=collections.Counter(tuple(r.get("каблук_вид") or ()) for r in в if є(r))
print("запис «є»:", sum(map(є,в)), "· каблук_вид серед них:", dict(вид.most_common(12)))
пл=[r for r in в if є(r) and "platform" in (r.get("каблук_вид") or ())]
print("запис «є» з видом platform:", len(пл), "· з них лише platform:", sum(1 for r in пл if tuple(r["каблук_вид"])==("platform",)))
у234=[r for r in в if є(r) and КБ.каблук(r.get("назва"),None,r.get("url"))["є"] is False]
print("у 234:", len(у234), "· з видом platform:", sum(1 for r in у234 if "platform" in (r.get("каблук_вид") or ())),
      "· типи:", dict(collections.Counter(r.get("тип") for r in у234).most_common(8)))
print("у 234 каблук_см розподіл:", dict(collections.Counter((r.get("каблук_см") is None) and "нема" or ("<2" if r["каблук_см"]<2 else ("2-3.9" if r["каблук_см"]<4 else "≥4")) for r in у234)))
