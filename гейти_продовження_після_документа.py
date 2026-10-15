"""Продовжує незмінені AST-оператори гейтів із місця FileNotFound; готові секції не повторює."""
import ast,importlib.util,sys
from pathlib import Path
root=Path('/workspace/dress3710-next/джерела');sys.path.insert(0,str(root))
p=root/'прилади/розділи_гейтів.py';tree=ast.parse(p.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
spec=importlib.util.spec_from_file_location('продовження_146_147',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import status
m.__dict__.update(_джр146=str(root),_ST72=status,_ast106=ast)
helper=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='_імпорти106')
moduleassign=next(n for n in main.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_модулі106' for t in n.targets))
start=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and n.value.args and isinstance(n.value.args[0],ast.Constant) and isinstance(n.value.args[0].value,str) and n.value.args[0].value.startswith('прилад лишається ПРИЛАДОМ'))
print('CHECKPOINT: лише незавершений останній тест §146 та §147; попередні два doc-тести НЕ повторюються')
fn=ast.FunctionDef(name='продовжити',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=main.body[start:],decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[moduleassign,helper,fn],type_ignores=[])),str(p),'exec'),m.__dict__)
raise SystemExit(m.продовжити())
