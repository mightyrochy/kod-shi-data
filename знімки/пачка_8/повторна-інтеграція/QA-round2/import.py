import builtins, contextlib, gc, gzip, hashlib, importlib.abc, importlib.util, io, json, pathlib, subprocess, sys, xml.etree.ElementTree as E
R=pathlib.Path('/tmp/liusterko-pachka-1310-4'); H=sys.argv[1]; OUT=pathlib.Path(__file__).parent
B=pathlib.Path('/workspace/scratch/qa-995-import-round2'); results=[]
for n in range(5191,5195):
    p=R/f'джерела/проби/дані_{n}.py'
    s=subprocess.check_output(['git','-C',str(R),'show',f'{H}:джерела/проби/дані_{n}.py']).decode()
    assert p.read_text()==s
    class Loader(importlib.abc.Loader):
        def create_module(self,spec): return None
        def exec_module(self,m): m.__file__=str(p); exec(compile(s,str(p),'exec'),m.__dict__)
    spec=importlib.util.spec_from_loader(f'qa999_{n}',Loader()); m=importlib.util.module_from_spec(spec)
    traps=[]; originals=[]
    def deny(*a,**kw): traps.append('IO'); raise AssertionError('Побічний IO під час імпорту')
    for obj,name in [(builtins,'open'),(io,'open'),(pathlib.Path,'resolve'),(pathlib.Path,'read_text'),(pathlib.Path,'read_bytes'),(pathlib.Path,'open'),(pathlib.Path,'write_text'),(pathlib.Path,'write_bytes'),(gzip,'decompress'),(E,'fromstring')]: originals.append((obj,name,getattr(obj,name)))
    stdout=io.StringIO();stderr=io.StringIO();sys.argv=['importer.py','--зберегти']
    try:
        for o,k,v in originals: setattr(o,k,deny)
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr): spec.loader.exec_module(m)
    finally:
        for o,k,v in originals: setattr(o,k,v)
    assert not traps and not stdout.getvalue() and not stderr.getvalue()
    save=[];stdout=io.StringIO();stderr=io.StringIO();sys.argv=[str(p),'--зберегти'];write=pathlib.Path.write_bytes
    def capture(target,b): save.append((str(target),b)); return len(b)
    try:
        pathlib.Path.write_bytes=capture
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr): exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
    finally: pathlib.Path.write_bytes=write
    payload=stdout.getvalue().encode();assert payload==(B/f'{n}-new.out').read_bytes();assert not stderr.getvalue();assert len(save)==1 and pathlib.Path(save[0][0]).read_bytes()==save[0][1]
    (OUT/f'{n}.out').write_bytes(payload)
    results.append({'проба':n,'рядків':len(s.splitlines()),'імпорт_IO':len(traps),'імпорт_stdout':0,'імпорт_stderr':0,'stdout_байтів':len(payload),'stdout_sha256':hashlib.sha256(payload).hexdigest(),'source_reference_exact':True,'створений_gzip_точний':True,'source_записів':0});print(n,'PASS')
    del m;gc.collect()
(OUT/'import.json').write_text(json.dumps({'head':H,'перевірки':results},ensure_ascii=False,indent=2)+'\n')
