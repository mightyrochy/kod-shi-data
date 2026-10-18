import ast,sys,os,json,warnings
warnings.simplefilter('ignore')
os.chdir(sys.argv[1]); всі={f[:-3] for f in os.listdir('.') if f.endswith('.py')}
def calls(мод, фн):
  t=ast.parse(open(мод+'.py').read())
  alias={}
  for n in ast.walk(t):
    if isinstance(n,ast.Import):
      for a in n.names:
        if a.name in всі: alias[a.asname or a.name]=a.name
    if isinstance(n,ast.ImportFrom) and n.module in всі:
      for a in n.names: alias[a.asname or a.name]=n.module+'.'+a.name
  for n in t.body:
    if isinstance(n,ast.FunctionDef) and n.name==фн:
      out=[]
      for c in ast.walk(n):
        if isinstance(c,ast.Call):
          f=c.func
          if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id in alias and '.' not in alias[f.value.id]:
            out.append(alias[f.value.id]+'.'+f.attr)
          elif isinstance(f,ast.Name) and f.id in alias: out.append(alias[f.id])
      seen=[];[seen.append(x) for x in out if x not in seen]
      return seen
for спец in sys.argv[2:]:
  м,ф=спец.split(':'); print(спец,'->',', '.join(calls(м,ф) or []))
