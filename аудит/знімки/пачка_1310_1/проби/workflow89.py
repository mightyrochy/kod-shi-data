from pathlib import Path
import ast, hashlib, json, os
root=Path('/tmp/liusterko-pachka-1310-1')
p=root/'джерела/прилади/розділи_гейтів.py'
source=p.read_text();tree=ast.parse(source)
main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
start=next(i for i,x in enumerate(main.body) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and getattr(x.value.func,'id',None)=='print' and x.value.args and isinstance(x.value.args[0],ast.Constant) and str(x.value.args[0].value).startswith('89. WORKFLOW'))
nodes=[];count=0
for node in main.body[start:]:
    nodes.append(node)
    if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and getattr(node.value.func,'id',None)=='тест':
        count+=1
        if count==2:break
assert count==2
test=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='тест')
space={'_os':os,'_тут':str(root/'джерела'),'ok':0,'збої':[],'пропущено':[]}
exec(compile(ast.Module(body=[test]+nodes,type_ignores=[]),str(p),'exec'),space)
assert space['ok']==2 and not space['збої'] and not space['пропущено']
result={'голова':'09ff6b7b5a46327666d633e1ba798f249941bb4d','початковий_прогін':{'пройдено':574,'впало':0,'без_входу':2},'причина':'sparse checkout не містив .github/workflows; файли додано без зміни HEAD','цільове_доповнення':{'секція':89,'пройдено':2,'впало':0,'без_входу':0,'workflow_файлів':len(space['_ямли89']),'код':'дослівні AST-вузли чинної main() та функції тест, без інших розділів','прилад_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'підсумок_без_повтору_батареї':{'пройдено':576,'впало':0,'без_входу':0}}
out=Path('/tmp/pachka-1310-evidence/доповнення-workflow89.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
