import json,subprocess,os,sys,time
SP='/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/V'; J=SP+'/wt/джерела'
fs=sys.argv[1:]
SN=open(SP+'/s/runprobes.py').read().split('SN="')[1].split('"\n')[0].replace('\\\\n','\\n')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8',PYTHONPATH=J)
out=open(SP+'/проби_повтор.jsonl','a')
for f in fs:
    t=time.time()
    r=subprocess.run(['timeout','600','python3','-c',SN.encode().decode('unicode_escape') if False else SN,f],cwd=J,capture_output=True,env=env,stdin=subprocess.DEVNULL)
    err=r.stderr.decode('utf-8','replace'); rc=r.returncode; cpu=None
    if '@@CPU' in err:
        tail=err.rsplit('@@CPU',1)[1].split(); cpu=float(tail[0]); rc=int(tail[2]); err=err.rsplit('@@CPU',1)[0]
    o=r.stdout.decode('utf-8','replace')+'\n--STDERR--\n'+err
    out.write(json.dumps(dict(f=f,code=rc,cpu=cpu,wall=round(time.time()-t,2),out=o[-1500:],outlen=len(o)),ensure_ascii=False)+'\n'); out.flush()
