import sys,pathlib,json,os,ast,subprocess
run=pathlib.Path(__file__).parent
src=pathlib.Path(sys.argv[1])
sys.path.insert(0,str(src));os.chdir(src)
import мовний_шар as M, пакет_моделі as P, дріт_моделі as W, паспорт_нагоди as N, сценарій as S, bridge as B
record=json.loads(pathlib.Path(sys.argv[3]).read_text(encoding='utf-8'))[0]
raw=next(v['відповідь'] for k,v in record['відповіді'].items() if 'seed3_01_' in k)
turn=json.loads(M.мова(json.dumps(dict(розмова={'нове':record['слова']},відповідь_моделі=raw,перша_відповідь=raw,завершити_договір=True))))
passport=M.паспорт_з_шару(turn['внутрішня'],{},слова_ходу=record['слова'],частини=turn['частини'])['паспорт']
scenario=N.з_показу({},passport)[0]
wire=W.випадок(P.випадок_для_пакета(passport,''))
inp=json.loads((src/'стенд_вх.json').read_text(encoding='utf-8'))
inp.update(паспорт=passport,сценарій={},каталог=str(pathlib.Path(sys.argv[2])),пакети=1,сід=3)
queries=json.loads(B.виклик('запити',json.dumps(inp,ensure_ascii=False)))
function=next(x for x in ast.walk(ast.parse((src/'міст_відповіді.py').read_text(encoding='utf-8'))) if isinstance(x,ast.FunctionDef) and x.name=='від_моделі')
result=dict(версія=src.parent.name,подія=passport.get('подія'),місце=passport.get('місце'),нагода=passport.get('нагода'),ошатність=passport.get('ошатність'),
            сценарій_є=S.є_сценарій(scenario),дріт=wire,пул_речей=queries.get('пул_речей'),пул_чому=queries.get('пул_чому'),помилка=queries.get('помилка'),
            кандидатів={k:len(v) for k,v in (queries.get('кандидати') or {}).items()},
            випадок_руки_1=((queries.get('пакети') or {}).get('1') or {}).get('випадок'),
            від_моделі={'рядків':function.end_lineno-function.lineno+1,'вузлів':len(list(ast.walk(function)))})
print(json.dumps(result,ensure_ascii=False),flush=True)
