import os,sys,signal
me=os.getpid(); pat=sys.argv[1]
for d in os.listdir('/proc'):
    if d.isdigit() and int(d)!=me:
        try: c=open('/proc/%s/cmdline'%d,'rb').read().decode('utf-8','replace').replace('\0',' ')
        except: continue
        if pat in c and 'kill.py' not in c and 'tm.py' not in c: print(d,c[:100]); os.kill(int(d),signal.SIGTERM)
