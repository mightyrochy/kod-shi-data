import ast,copy,hashlib,json,subprocess
from pathlib import Path
r=Path('/workspace/replace4945');o=Path(__file__).parent
base='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be';head='b722c8867f671c612e71c5f5828f8befbf642111'
def read(ref,f):return subprocess.check_output(['git','-C',str(r),'show',ref+':джерела/'+f]).decode()
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
a=read(base,'показ.html');b=read(head,'показ.html');marker='async function зібратиОбразиП()'
assert a[a.index(marker):]==b[b.index(marker):]
checks=[]
for f,names in [('пакет_моделі.py',['промпт_складання']),('уважний_вибір.py',['_контекст','_запит','скласти_за_оцінками']),('міст_відповіді.py',['від_моделі'])]:
 trees=[ast.parse(read(v,f)) for v in [base,head]]
 for name in names:
  old,new=[next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==name) for t in trees]
  removed=[];body=[]
  for node in new.body:
   if isinstance(node,ast.If) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='get' and x.args and isinstance(x.args[0],ast.Constant) and x.args[0].value in ('заміна','слот_заміни','replacement') for x in ast.walk(node.test)):
    removed.append(ast.unparse(node.test))
   else: body.append(node)
  new.body=body
  assert removed and ast.dump(old)==ast.dump(new),(f,name)
  checks.append({'file':f,'function':name,'unchangedWithoutLocalReplacementBranch':True,'localOnlyConditions':removed})
result={'head':head,'base':base,'fullAssemblyHtmlSuffixExact':True,'fullAssemblyHtmlSuffixSHA256':sha(b[b.index(marker):]),'fullAssemblyFunction':'зібратиОбразиП','existingPathFunctions':checks}
(o/'full-path-check-v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
