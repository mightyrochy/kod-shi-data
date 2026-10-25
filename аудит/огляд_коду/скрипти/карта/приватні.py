import ast,os,sys,json,glob,warnings;warnings.simplefilter('ignore')
os.chdir(sys.argv[1]); g=json.load(open(sys.argv[2])); Я=set(g['ядро'])
def розібрати(files):
  res={}; err=0
  for f in files:
    try: res[f]=ast.parse(open(f,encoding='utf-8').read())
    except Exception: err+=1
  return res,err
def псевдоніми(t):
  alias={}
  for n in ast.walk(t):
    if isinstance(n,ast.Import):
      for a in n.names:
        if a.name in Я: alias[a.asname or a.name]=a.name
  return alias
def приватний(n):
  return n.attr.startswith('_') and not n.attr.startswith('__')
def scan(files,дерева=None):
  # дерева — всі розібрані файли, де шукаємо виклики: модуль, переданий ПАРАМЕТРОМ, ховає `X._y` від псевдонімів імпорту (9053)
  tot=0; names=set(); fl=0
  мої,err=розібрати(files)
  усі=дерева if дерева is not None else мої
  мої={f:усі.get(f,t) for f,t in мої.items()}   # ті самі вузли, що в `усі`: параметри шукаємо за id
  # ім'я функції → її параметри, і яким параметрам хоч раз передано модуль ядра (позиційно чи іменованим аргументом)
  функції={}
  for t in усі.values():
    for n in ast.walk(t):
      if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): функції.setdefault(n.name,[]).append(n)
  модульні_параметри={}   # (id вузла функції) → {параметр: модуль}
  for t in усі.values():
    al=псевдоніми(t)
    for n in ast.walk(t):
      if not isinstance(n,ast.Call): continue
      ім=n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else None
      for ф in функції.get(ім,[]):
        пар=[a.arg for a in ф.args.posonlyargs+ф.args.args]
        if пар and пар[0] in ('self','cls'): пар=пар[1:]
        for i,a in enumerate(n.args):
          if isinstance(a,ast.Name) and a.id in al and i<len(пар): модульні_параметри.setdefault(id(ф),{})[пар[i]]=al[a.id]
        for k in n.keywords:
          if k.arg and isinstance(k.value,ast.Name) and k.value.id in al: модульні_параметри.setdefault(id(ф),{})[k.arg]=al[k.value.id]
  for f,t in мої.items():
    alias=псевдоніми(t)
    for n in ast.walk(t):
      if isinstance(n,ast.ImportFrom) and n.module in Я:
        for a in n.names:
          if a.name.startswith('_'): tot+=1; names.add(n.module+'.'+a.name)
    k=0
    for n in ast.walk(t):
      if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in alias and приватний(n):
        k+=1; names.add(alias[n.value.id]+'.'+n.attr)
      if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and id(n) in модульні_параметри:
        м=модульні_параметри[id(n)]
        for x in ast.walk(n):
          if isinstance(x,ast.Attribute) and isinstance(x.value,ast.Name) and x.value.id in м and x.value.id not in alias and приватний(x):
            k+=1; names.add(м[x.value.id]+'.'+x.attr)
    tot+=k; fl+= (k>0)
  return tot,len(names),fl,len(files)-len(мої)
корінь=[f for f in glob.glob('*.py') if f[:-3] not in Я]
print('корінь не-ядро (%d файлів): звертань до приватних імен ядра %d, різних імен %d, файлів %d'%((len(корінь),)+scan(корінь)[:3]))
пр=glob.glob('проби/**/*.py',recursive=True)
r=scan(пр); print('проби (%d файлів): звертань %d, різних імен %d, файлів %d, не розібрано %d'%((len(пр),)+r))
# ядро → приватні інших модулів ядра
r=scan([м+'.py' for м in Я],розібрати(glob.glob('*.py')+glob.glob('проби/**/*.py',recursive=True))[0]); print('ядро→ядро приватні:',r[:2])
