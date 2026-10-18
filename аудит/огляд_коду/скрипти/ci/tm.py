#!/usr/bin/env python3
import sys,os,time,resource,subprocess
n=sys.argv[1]; cmd=sys.argv[2:]
l=os.getloadavg()
t=time.time()
p=subprocess.run(['nice','-n','10']+cmd,stdout=open(f'../../logs/{n}.out','w'),stderr=open(f'../../logs/{n}.err','w'))
w=time.time()-t
r=resource.getrusage(resource.RUSAGE_CHILDREN)
print(f'{n}\trc={p.returncode}\twall={w:.1f}s\tuser={r.ru_utime:.1f}\tsys={r.ru_stime:.1f}\tmaxrss={r.ru_maxrss/1024:.0f}MB\tload0={l[0]:.2f}',flush=True)
