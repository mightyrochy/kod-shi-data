"""3.5/8030/8661: фрази в аргументах trace.запис і в ярликах акценту; AST, без читання слів моделлю."""
import ast, pathlib, re, subprocess, sys
корінь = pathlib.Path(__file__).resolve().parents[1]
фраза = lambda в: isinstance(в, ast.Constant) and isinstance(в.value, str) and bool(re.search(r'[а-яіїєґ].*\s|\s.*[а-яіїєґ]', в.value, re.I))
лічба = dict(trace_фраз=0, trace_динамічних=0, ярликів_фраз=0)
for п in корінь.glob('*.py'):
    текст = subprocess.check_output(['git', 'show', sys.argv[1]+':джерела/'+п.name], text=True) if len(sys.argv)>1 and п.name!='statements.py' else п.read_text()
    дерево = ast.parse(текст)
    імена = {а.asname or а.name for в in дерево.body if isinstance(в, ast.Import) for а in в.names if а.name=='trace'}
    for в in ast.walk(дерево):
        if not isinstance(в, ast.Call): continue
        if п.name=='суд_від_моделі.py' and isinstance(в.func, ast.Name) and в.func.id=='_дод' and len(в.args)>2:
            лічба['ярликів_фраз'] += sum(фраза(з) for з in ast.walk(в.args[2]))
        слід = isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) and в.func.value.id in імена and в.func.attr=='запис'
        for к in в.keywords:
            if слід and к.arg in ('напрям','значення'):
                лічба['trace_фраз'] += фраза(к.value)
                лічба['trace_динамічних'] += isinstance(к.value, (ast.JoinedStr, ast.BinOp))
            if п.name in ('palettes.py','суд_від_моделі.py') and к.arg=='ярлик':
                лічба['ярликів_фраз'] += sum(фраза(з) for з in ast.walk(к.value))
print(лічба)
