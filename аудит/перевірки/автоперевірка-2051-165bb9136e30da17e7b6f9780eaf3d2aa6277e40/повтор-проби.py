"""Повторює окрему пробу в заданому дереві й зберігає точний журнал."""
import gzip,json,os,pathlib,subprocess,sys,time
root=pathlib.Path(sys.argv[1]); probe=sys.argv[2]; out=pathlib.Path(sys.argv[3]); tag=sys.argv[4]
env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONHASHSEED='0')
start=time.monotonic()
p=subprocess.run([sys.executable,probe],cwd=root/'джерела',env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out/(tag+'.txt.gz')).write_bytes(gzip.compress(p.stdout,mtime=0))
r=dict(команда=[sys.executable,probe],код=p.returncode,секунд=round(time.monotonic()-start,1),дерево=str(root))
(out/(tag+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(p.stdout.decode('utf-8',errors='replace'))
print(json.dumps(r,ensure_ascii=False))
sys.exit(p.returncode)