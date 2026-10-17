const fs=require('fs');
const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
(async()=>{
const b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
try {
const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:1});
const html=fs.readFileSync('/tmp/latin3760-1710-after.html','utf8');
const base=require('child_process').execFileSync('git',['show','66e29b6534290e438ae814f7f3db1e230cc2c920:джерела/показ.html'],{cwd:'/tmp/latin3760-1710',encoding:'utf8',maxBuffer:6000000});
const old=base.match(/function законніКарткиП\(.*?\n\}\n/s)[0];
const before=html.replace(/function законніКарткиП\(.*?\n\}\n/s,old).replace('законніКарткиП(new Set([...своїТ(ключ), ...дозволені]))','законніКарткиП(к, new Set([...своїТ(ключ), ...дозволені]))');
for (const mode of ['before','after']) {
const p=await c.newPage();
await p.route('**/*',r=>r.request().url().startsWith('http://local.test/')?r.fulfill({contentType:'text/html',body:mode==='before'?before:html}):r.abort());
await p.goto('http://local.test/'+mode,{waitUntil:'domcontentloaded'});
await p.waitForFunction(()=>typeof мовоюКарткуП==='function');
await p.waitForTimeout(800);
const out=await p.evaluate(async(mode)=>{

const к={рука:1,текст:'White top, neutral trousers and sneakers in a casual everyday outfit.',опис:'White top, neutral trousers and sneakers in a casual everyday outfit.',як_носити:[],свідомі:[],речі:[{id:'3760',назва:'Кросівки Nike',крамниця:'VOVK',ціна:1000}]};
let calls=[];
мовоюП=async function(т,де){calls.push(де);const тексти=Object.fromEntries(Object.keys(т).map(k=>[k,'Піна EVA добре пом’якшує кожен крок під час довгої міської прогулянки. Річ Nike з VOVK чудово поєднується з білим верхом та світлими штанами, колготи 40 den, V-подібний виріз.'])); return {тексти,записи:[{вхід:т,вихід:тексти}]};};
повідомленнямП=async()=>({тексти:{},записи:[]});
await мовоюКарткуП(к,'hand_1');
П={в:'ПОКАЗ-V1',картки:[к],збірка:'3760',каталог:'цільова проба',профіль:'',сценарій:{},палітра:{}};
рендер();
return {calls,опис:к.опис,текст:к.текст,знята:к.латиниця_знята||{},visible:document.getElementById('к-0').innerText};
},mode);
await p.waitForTimeout(150);
await p.evaluate(()=>режим('образи'));
await p.screenshot({path:'/tmp/latin3760-1710-'+mode+'-390.png',fullPage:false});
console.log(JSON.stringify({mode,...out}));
await p.close();
}
await c.close();
} finally {await b.close();}
})();
