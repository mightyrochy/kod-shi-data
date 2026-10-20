const fs = require('fs'), path = require('path'), cp = require('child_process');
const { chromium } = require('playwright');
const root = process.cwd(), dir = path.resolve(process.argv[2] || path.join(root, 'work/1452'));
// Зібрана сторінка — у dir/index.html; мережу й моделі runner не викликає.
const photoRaw = cp.execFileSync('git', ['show', '6054d890385c850cca1f0af7865bd1bfd8854aaf:аудит/живі_1452/ж7_прогулянка_субота/VIDPOVIDI/seed3_35_ОЦІНКА_речі_на_фото.txt'], {encoding:'utf8'}).split('── ВІДПОВІДЬ', 2)[1].split('──\n', 2)[1].trim();
const base = {};
for (const name of ['колір_відношення', 'протокол']) base[name] = cp.execFileSync('git', ['show', '7082932c:джерела/' + name + '.py'], {encoding:'utf8'});
const profiles = Object.fromEntries(['ж3','ж7'].map(id => [id, JSON.parse(fs.readFileSync(path.join(root,'аудит/проби/жінки',id+'.json'),'utf8'))]));
const py = `
import json, colorspace as cs, palettes as PAL, міст_основи as MO, протокол as PR, оцінка_образу as OC
P=json.loads(_profiles)
arc=(160.,184.)
spec={s:dict(роль=r,L=[5,95],C=[14.,34.],дуга_тону=arc) for s,r in (("верх","домінанта"),("низ","секундант"),("взуття","секундант"),("сумка","акцент"))}
spec["_схема"]="тональна"
import суд_від_моделі as SV
item=lambda i,s,L,C,h:dict(id=i,слот=s,lab=list(SV._lab_з(L,C,h)))
looks=[[item("v","верх",85,2,80),item("n","низ",25,2,260),item("b","сумка",50,30,172)], [item("v","верх",70,20,170),item("n","низ",45,18,175),item("b","сумка",50,30,172)]]
tonal=[dict(тон=PAL.тон_тональної(items,spec),вийшла=not bool(PAL.повідомлення_схеми_жінці(items,spec)),знахідок=len(PAL.обіцянка_схеми(items,spec))) for items in looks]
assert [x["вийшла"] for x in tonal]==[False,True]
profile=P["ж7"]
F=cs.features([cs.hx(x) for x in profile["skin"]],[cs.hx(x) for x in profile["hair"]],cs.hx(profile["eyes"]))
bases=MO._основи(F)
rank=[{k:x.get(k) for k in ("ключ","hex","бал","осі")} for x in sorted(bases["рекомендовані"],key=lambda x:-x["бал"])[:12]]
assert rank and all(x["бал"]>=.5 for x in rank)
parsed,why,notes=PR.розбір_за_схемою(_assembly,"ОБРАЗИ_V1")
photo=OC.речі_з_відповіді(_photo,[dict(ід="ф1"),dict(ід="ф2")])
result=dict(ж3_театр_тональна=tonal,ж7_прогулянка_субота=rank,raw_образів=len((parsed or {}).get("образи",[])),raw_рамок=sum(bool(x["рамка"]) for x in photo["речі"]),raw_речей=len(photo["речі"]),нормалізовано=notes)
json.dumps(result,ensure_ascii=False)
`;
(async()=>{
const browser = await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const results={};
for(const mode of ['ДО','ПІСЛЯ']){
 const page = await browser.newPage({viewport:{width:390,height:844}});
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname==='127.0.0.1') {
   if(url.pathname==='/') return route.fulfill({status:200,contentType:'text/html',body:fs.readFileSync(path.join(dir,'index.html'))});
   return route.fulfill({status:404,body:''});
  }
  if(url.href.includes('/pyodide/')){
   const name=path.basename(url.pathname), file=path.join('/workspace/work/pyodide',name);
   if(fs.existsSync(file)) return route.fulfill({status:200,contentType:name.endsWith('.wasm')?'application/wasm':name.endsWith('.js')?'application/javascript':'application/octet-stream',body:fs.readFileSync(file)});
  }
  return route.abort();
 });
 await page.goto('http://127.0.0.1:1452');
 await page.evaluate(async()=>{await підняти_міст_показу();});
 results[mode]=JSON.parse(await page.evaluate(async ({mode,base,profiles,py,assembly,photo})=>{
  if(mode==='ДО') for(const [name,source] of Object.entries(base)){
   pyodide_показу.globals.set('_old_source',source);
   await pyodide_показу.runPythonAsync('import importlib\n_old_module=importlib.import_module('+JSON.stringify(name)+')\nexec(compile(_old_source,"7082932c/'+name+'.py","exec"),_old_module.__dict__)');
  }
  pyodide_показу.globals.set('_profiles',JSON.stringify(profiles));
  pyodide_показу.globals.set('_assembly',assembly);
  pyodide_показу.globals.set('_photo',photo);
  return await pyodide_показу.runPythonAsync(py);
 },{mode,base,profiles,py,assembly:fs.readFileSync(path.join(root,'джерела/проби/дані_1452/складання.json'),'utf8'),photo:photoRaw}));
 await page.evaluate(async profile=>{
  КОЛІР.шкіра=profile.skin[0];КОЛІР.волосся=profile.hair[0];КОЛІР.очі=profile.eyes;
  вхідПалітри=()=>({шкіра:profile.skin,волосся:profile.hair,очі:profile.eyes,зріст:160,обхвати:Object.fromEntries(Object.entries(profile.мірки).filter(([k])=>k!=="зріст")),сід:3,без_фото:true});
  режим('палітра');
  await оновитиПалітруП();
 },profiles['ж7']);
 await page.locator('#пал-основа').scrollIntoViewIfNeeded();
 await page.evaluate(()=>document.querySelector('#пал-основа').scrollIntoView({block:'start'}));
 await page.screenshot({path:path.join(dir,mode+'_ж7_390x844.png'),fullPage:false});
 results[mode].чипів_на_екрані=await page.locator('#пал-основа > .чип').count();
 if(!results[mode].чипів_на_екрані) throw new Error(await page.locator('#пал-стан').innerText());
 console.log(mode,JSON.stringify(results[mode]));
 await page.close();
}
fs.writeFileSync(path.join(dir,'функції.json'),JSON.stringify(results,null,2));
if(JSON.stringify(results['ДО'].ж3_театр_тональна)!==JSON.stringify(results['ПІСЛЯ'].ж3_театр_тональна)||JSON.stringify(results['ДО'].ж7_прогулянка_субота)!==JSON.stringify(results['ПІСЛЯ'].ж7_прогулянка_субота)) throw new Error('Функції сцен відрізняються');
if(results['ДО'].raw_образів!==1||results['ПІСЛЯ'].raw_образів!==10)throw new Error('Пропозиція 7590 не відновила набір');
await browser.close();
console.log('Дві функціональні сцени ДО=7082932c/ПІСЛЯ=5fe2e3fc, 0 викликів моделей, рамки лишаються відкритими');
})().catch(e=>{console.error(e);process.exit(1)});
