import os,sys,subprocess,time,json,glob,random
from concurrent.futures import ThreadPoolExecutor
W=sys.argv[1]; OUT=sys.argv[2]; J=W+'/джерела'
fs=sorted(os.path.basename(f) for f in glob.glob(J+'/проби/*.py'))
random.Random(7).shuffle(fs)
import re
def heavy(f):
    s=open(J+'/проби/'+f,encoding='utf-8').read()
    return bool(re.search(r'каталог_на_диску|каталог_brief|каталог_повний|import[^\n]*\b(feed|Ф)\b|from feed|стенд_знімок|тест_живого|zhnyvarka|requests|urllib|ComfyUI',s))
random.Random(11).shuffle(fs)
done=set()
if os.path.exists(OUT): done={json.loads(l)['f'] for l in open(OUT)}
fs=[f for f in fs if f not in done]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
SN="import resource,subprocess,sys,os;os.nice(19);resource.setrlimit(resource.RLIMIT_CPU,(60,65));p=subprocess.run(['python3','-W','ignore','проби/'+sys.argv[1]],capture_output=True,stdin=subprocess.DEVNULL);u=resource.getrusage(resource.RUSAGE_CHILDREN);sys.stdout.buffer.write(p.stdout);sys.stderr.buffer.write(p.stderr);sys.stderr.write('\\n@@CPU %.2f RC %d\\n'%(u.ru_utime+u.ru_stime,p.returncode))"
def run2(f):
    t=time.time(); cpu=None
    try:
        r=subprocess.run(['timeout','600','python3','-c',SN,f],cwd=J,capture_output=True,env=env,stdin=subprocess.DEVNULL)
        err=r.stderr.decode('utf-8','replace'); rc=r.returncode
        if '@@CPU' in err:
            tail=err.rsplit('@@CPU',1)[1].split(); cpu=float(tail[0]); rc=int(tail[2]); err=err.rsplit('@@CPU',1)[0]
        o=(r.stdout.decode('utf-8','replace')+'\n--STDERR--\n'+err); code=rc
    except Exception as e: code=-1; o=repr(e)
    return dict(f=f,code=code,cpu=cpu,wall=round(time.time()-t,2),out=o[-1500:],outlen=len(o))
with open(OUT,'a') as fo, ThreadPoolExecutor(2) as ex:
    for r in ex.map(run2,fs):
        fo.write(json.dumps(r,ensure_ascii=False)+'\n'); fo.flush()
