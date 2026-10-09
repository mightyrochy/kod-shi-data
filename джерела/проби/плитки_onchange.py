"""Проба: зміна поля сценарію в справжньому Chromium кличе хідПлитокУФоніП (так), до зміни — ні.
Запуск: NODE_PATH=<тека з playwright> python3 плитки_onchange.py <зібраний.html>"""
import json, subprocess, sys, tempfile, os
js = r"""
const { chromium } = require('playwright');
(async()=>{
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p = await b.newPage({viewport:{width:390,height:844}});
  await p.route(/^https?:/, r=>r.abort());
  await p.goto('file://'+process.argv[2]); await p.waitForTimeout(3000);
  const r = await p.evaluate(async()=>{
    const out={}; let n=0; window.хідПлитокУФоніП=()=>{n++;};
    out.до=n;
    for (const id of ['сц-місце','сц-дрес','сц-темп','сц-вітер','сц-опади','сц-реагенти']){
      const e=document.getElementById(id); if(!e){out[id]='нема';continue;}
      const before=n;
      if(e.tagName==='SELECT' && e.options.length>1) e.selectedIndex=(e.selectedIndex+1)%e.options.length; else e.value=e.value||'x';
      e.dispatchEvent(new Event('change',{bubbles:true}));
      await new Promise(r=>setTimeout(r,150));
      out[id]=n-before;
    }
    return out;});
  console.log(JSON.stringify(r)); await b.close();
})();
"""
f=os.path.join(tempfile.mkdtemp(),'p.js'); open(f,'w').write(js)
env=dict(os.environ,NODE_PATH=os.environ.get('NODE_PATH',''))
r=subprocess.run(['node',f,os.path.abspath(sys.argv[1])],env=env,capture_output=True,text=True,timeout=120)
print(r.stdout.strip() or r.stderr[-300:])
