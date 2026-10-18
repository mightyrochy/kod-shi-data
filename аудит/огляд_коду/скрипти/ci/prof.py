import sys,os,time,cProfile,pstats,runpy,io; sys.modules.pop("profile",None)
n=sys.argv[1]; script=sys.argv[2]; sys.argv=[script]+sys.argv[3:]
sys.path.insert(0,os.path.dirname(os.path.abspath(script)) if not script.startswith('прилади') else os.getcwd())
sys.path.insert(0,os.getcwd())
t0=time.time()
class S:
    def __init__(s,o): s.o=o; s.buf=''
    def write(s,x):
        s.buf+=x
        while '\n' in s.buf:
            l,s.buf=s.buf.split('\n',1)
            s.o.write('%7.1f %s\n'%(time.time()-t0,l))
    def flush(s): s.o.flush()
out=open(f'../../logs/stamp_{n}.txt','w')
sys.stdout=S(out)
pr=cProfile.Profile(); pr.enable()
try: runpy.run_path(script,run_name='__main__')
except SystemExit as e: rc=e.code
else: rc=0
pr.disable()
sys.stdout=sys.__stdout__
pr.dump_stats(f'../../logs/prof_{n}.bin')
print(n,'rc',rc,'wall %.1f'%(time.time()-t0))
