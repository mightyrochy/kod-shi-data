import json,pathlib,sys
sys.stdout.reconfigure(encoding='utf8')
root=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(root/'джерела'))
import пара_взуття as P
cases=[('мовчання',{},None),('нижче порога',{'каблук_см':3},None),
 ('на порозі',{'каблук_см':4},True),('нуль',{'каблук_см':0},False),
 ('сама платформа',{'каблук_вид':['platform']},None),
 ('платформа і клас',{'каблук_вид':['platform'],'каблук_рівень':['mid']},True),
 ('плаский клас',{'каблук_рівень':['flat']},False),
 ('шпилька без числа',{'каблук_вид':['stiletto']},True),
 ('низький каблук словом',{'каблук_см':3,'каблук_рівень':['low']},True),
 ('тип без каблука',{'тип':'кеди'},False)]
records=[]
for name,fields,expected in cases:
 r=dict(fields,id=name,слот='взуття')
 actual,source=P.каблук(r)
 no,_,_=P.відсів([r],'нема')
 yes,_,_=P.відсів([r],'є')
 ok=actual is expected and bool(no)==(expected is not True) and bool(yes)==(expected is not False)
 records.append(dict(ситуація=name,вхід=fields,очікується=expected,факт=actual,джерело=source,пройдено=ok))
print(json.dumps(records,ensure_ascii=False,indent=2))
assert all(r['пройдено'] for r in records)
