const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const БАЗА='http://127.0.0.1:8765', ПИО='/tmp/pyodide', ІДХ='/tmp/стенд/index.html';
(async()=>{
  const br=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'}); const pg=await br.newPage({viewport:{width:390,height:844}});
  await pg.route('https://cdn.jsdelivr.net/pyodide/**',async r=>{const ім=new URL(r.request().url()).pathname.split('/').pop();const f=path.join(ПИО,ім);
    if(!fs.existsSync(f)) return r.fulfill({status:404,body:'нема'});
    r.fulfill({status:200,contentType:ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream',body:fs.readFileSync(f)});});
  await pg.route(u=>new URL(u).origin===БАЗА,r=>r.fulfill({status:200,contentType:'text/html; charset=utf-8',body:fs.readFileSync(ІДХ)}));
  await pg.route(u=>!/127\.0\.0\.1|cdn\.jsdelivr\.net\/pyodide/.test(u.href),r=>r.abort());
  await pg.goto(БАЗА+'/index.html'); await pg.waitForTimeout(1500);
  const o=await pg.evaluate(async()=>{ const p=await підняти_міст_показу(); return p.runPython(`
import json,colorspace as cs,palettes as P
from суд_від_моделі import розібрати_рядок_блокера as R, рядок_блокера as RB, _ЧОМУ_БЛОКЕРА as Ч
def лаб(h): return cs.to_lab(tuple(int(h[i:i+2],16) for i in (1,3,5)))
хекс={h:P._назва(лаб(h))[0] for h in ["#E6DCCD","#FFD700","#D3D3D3","#8C97A6","#3C2E2A","#FFFFFF","#000000","#808080"]}
бл={r:R(r) for r in [RB("нема_взуття"),RB("слот_двічі","верх"),RB("слот_двічі","комплект",ще=["верх","низ"]),"неповний:третя_річ","нема_верхнього_шару","нема взуття — без взуття образ не готовий","чужий гейт"]}
json.dumps({"hex":хекс,"блокери":{k:[v[0],v[1]] for k,v in бл.items()},"коди_без_заяви":[k for k in Ч if not k]},ensure_ascii=False)`);});
  console.log(o); await br.close();
})();
