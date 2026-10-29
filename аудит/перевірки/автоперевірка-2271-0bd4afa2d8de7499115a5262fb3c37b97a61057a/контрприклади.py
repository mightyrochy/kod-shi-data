import ast, importlib.util, tempfile, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('prylad',root/'джерела/прилади/корінь_річ_колір_межі.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
path=root/'джерела/колір_простір_риси.py'
text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='підтон_риси')
z=m.Збір(); m.обхід_python(str(path),'джерела/колір_простір_риси.py',z,set(),{'тепло'})
print('підтон_риси: у_кольорі =',m.у_кольорі(f.body,'джерела/колір_простір_риси.py'))
for n in ast.walk(f):
    if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='h':
        print(f'рядок {n.lineno}: {ast.unparse(n)}; ознака = {m.ознаки_п1_межа_числом(n)}; знайдено =',('джерела/колір_простір_риси.py',n.lineno) in z.м)

with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
    p=Path(tmp)/'колір_проба.py'
    for name,code in [
        ('звичайне присвоєння','ДУГА = (20, 80)\n'),
        ('анотоване присвоєння','ДУГА: tuple = (20, 80)\n'),
        ('звичайна таблиця',"ВІКНА = {'red': (10,90,5,60,(0,30)), 'green': (10,90,5,60,(90,160)), 'blue': (10,90,5,60,(220,280))}\n"),
        ('анотована таблиця',"ВІКНА: dict = {'red': (10,90,5,60,(0,30)), 'green': (10,90,5,60,(90,160)), 'blue': (10,90,5,60,(220,280))}\n"),
    ]:
        p.write_text(code,encoding='utf-8'); z=m.Збір(); m.обхід_python(str(p),'джерела/колір_проба.py',z,set(),set())
        print(name,': місць',len(z.м),'; пункти',sorted({v for r in z.м.values() for v in r['пункти']}))
    js=Path(tmp)/'колір.js'
    for name,code in [
        ('JS, звичайний виклик','function тон(lab) { return Math.atan2(lab[2], lab[1]); }\n'),
        ('JS, копія LCh→Lab','function lab(L,C,h) { const r=h*Math.PI/180; return [L,C*Math.cos(r),C*Math.sin(r)]; }\n'),
        ('JS, RGB→сім’я','function family(r,g,b) { return r > g && r > b ? "red" : "other"; }\n'),
    ]:
        js.write_text(code,encoding='utf-8'); z=m.Збір(); m.обхід_js(str(js),'джерела/показ/колір.js',z)
        print(name,': місць',len(z.м))
