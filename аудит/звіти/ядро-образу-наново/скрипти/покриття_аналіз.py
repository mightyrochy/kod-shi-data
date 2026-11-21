# Рядки у виконаних функціях за модулями замикання. Запуск з кореня репозиторію після граф.py і покриття.py:
#   python3 -I аудит/звіти/ядро-образу-наново/скрипти/покриття_аналіз.py джерела /tmp/граф.json /tmp/покриття.json /tmp/покриття_мод.json
import json, ast, os, sys, collections
ДЖ=sys.argv[1]; г=json.load(open(sys.argv[2]))
вик=json.load(open(sys.argv[3]))
за_мод=collections.defaultdict(set)
for f,л,q in вик: за_мод[f].add(л)
рез={}
for м in г['м']:
    ф=м+'.py'; src=open(os.path.join(ДЖ,ф),encoding='utf-8').read(); t=ast.parse(src)
    всього=len(src.splitlines()); фун=0; фун_вик=0; фун_n=0; фун_n_вик=0
    def обійти(тіло):
        global фун, фун_вик, фун_n, фун_n_вик
        for n in тіло:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                поч=min([n.lineno]+[d.lineno for d in n.decorator_list]); дов=n.end_lineno-поч+1
                фун+=дов; фун_n+=1
                if n.lineno in за_мод[ф] or поч in за_мод[ф]: фун_вик+=дов; фун_n_вик+=1
            elif isinstance(n,ast.ClassDef): обійти(n.body)
            elif isinstance(n,(ast.If,ast.Try)):
                обійти(n.body); обійти(getattr(n,'orelse',[]))
    обійти(t.body)

    рез[м]=dict(всього=всього,фун=фун,фун_вик=фун_вик,n=фун_n,n_вик=фун_n_вик,імпорт=(ф in за_мод))
json.dump(рез,open(sys.argv[4],'w'),ensure_ascii=False)
S=lambda k: sum(r[k] for r in рез.values())
print('модулів',len(рез),'рядків',S('всього'),'у функціях',S('фун'),'у виконаних функціях',S('фун_вик'),'функцій',S('n'),'виконано',S('n_вик'))
print('модулів з хоч однією виконаною функцією', sum(1 for r in рез.values() if r['n_вик']), 'без жодної', sum(1 for r in рез.values() if not r['n_вик']))
ряд=sorted(рез.items(),key=lambda x:-x[1]['фун_вик'])
print('топ за рядками виконаних функцій:')
for м,r in ряд[:30]: print(f"  {м} {r['всього']} фун {r['фун']} вик {r['фун_вик']} ({r['n_вик']}/{r['n']})")
print('модулі без жодної виконаної функції:', ' '.join(f"{м}({r['всього']})" for м,r in рез.items() if not r['n_вик']))
