import os,subprocess,pathlib,json,time,signal
root=pathlib.Path('/workspace/replace4945');src=root/'джерела';out=pathlib.Path('/workspace/replace4945-ui-final-evidence/батарея');head='b722c8867f671c612e71c5f5828f8befbf642111'
def actual():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()
assert actual()==head
result=json.loads((out/'результати.json').read_text());assert not any(x['етап']=='заміна4945' for x in result['resume']['steps']); result['resume']['probeWrapperPID']=os.getpid();result['успіх']=False
p=out/'результати.json'
def save():p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
save();env=dict(os.environ,NODE_PATH='/workspace/kod-shi-data/джерела/node_modules',TMPDIR='/workspace/replace4945-tmp');env.pop('LYUSTERKO_CATALOG',None)
for name,cmd in [('заміна4945',['python3','-u','проби/заміна_4945.py'])]:
 assert actual()==head
 row={'етап':name,'head_before':actual(),'command':cmd,'timeout_seconds':300,'started_utc':time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime())};result['resume']['steps'].append(row);save();start=time.time()
 with (out/(name+'.log')).open('w') as log:
  proc=subprocess.Popen(cmd,cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);row['pid']=proc.pid;save();print('START',name,proc.pid,flush=True)
  try:rc=proc.wait(timeout=300)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGTERM)
   try:proc.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
   rc=124;row['timed_out']=True
 row['код']=rc;row['seconds']=round(time.time()-start,1);row['head_after']=actual();save();print('END',row,flush=True)
 if rc:raise SystemExit(rc)
 result['steps'].append({'етап':name,'команда':cmd,'код':rc,'секунди':row['seconds'],'resumed_only_unfinished':True});save()
assert actual()==head
result['успіх']=False;result['blocker']='reach resume timeout300s/rc124; no NIKHTO result';result['own_background_jobs_after_completion']=0;save();print('Ownprobe complete; battery BLOCKED reach124, earlier rc0 retained, ownjobs0',flush=True)
