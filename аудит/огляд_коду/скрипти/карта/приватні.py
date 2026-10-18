import ast,os,sys,json,glob,warnings;warnings.simplefilter('ignore')
os.chdir(sys.argv[1]); g=json.load(open(sys.argv[2])); Я=set(g['ядро'])
def scan(files):
  tot=0; names=set(); fl=0; err=0
  for f in files:
    try: t=ast.parse(open(f,encoding='utf-8').read())
    except Exception: err+=1; continue
    alias={}
    for n in ast.walk(t):
      if isinstance(n,ast.Import):
        for a in n.names:
          if a.name in Я: alias[a.asname or a.name]=a.name
      if isinstance(n,ast.ImportFrom) and n.module in Я:
        for a in n.names:
          if a.name.startswith('_'): tot+=1; names.add(n.module+'.'+a.name)
    k=0
    for n in ast.walk(t):
      if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in alias and n.attr.startswith('_') and not n.attr.startswith('__'):
        k+=1; names.add(alias[n.value.id]+'.'+n.attr)
    tot+=k; fl+= (k>0)
  return tot,len(names),fl,err
корінь=[f for f in glob.glob('*.py') if f[:-3] not in Я]
print('корінь не-ядро (%d файлів): звертань до приватних імен ядра %d, різних імен %d, файлів %d'%((len(корінь),)+scan(корінь)[:3]))
пр=glob.glob('проби/**/*.py',recursive=True)
r=scan(пр); print('проби (%d файлів): звертань %d, різних імен %d, файлів %d, не розібрано %d'%((len(пр),)+r))
# ядро → приватні інших модулів ядра
r=scan([м+'.py' for м in Я]); print('ядро→ядро приватні:',r[:2])
