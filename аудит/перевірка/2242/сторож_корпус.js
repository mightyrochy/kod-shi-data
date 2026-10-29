// Прогін сторожа виходу (голова пачки) по справжньому видимому тексту серії 2: скільки рядків став би шаблоном.
const fs=require('fs'), path=require('path');
const {JSDOM}=require('jsdom'); const {IDBFactory,IDBKeyRange}=require('fake-indexeddb');
const [,, джерела, ...файли]=process.argv;
const {прочитатиДовідникJSON,підставитиШаблон,зібратиШаблонПоказу}=require(path.join(джерела,'показ_шаблон.js'));
let html=підставитиШаблон(зібратиШаблонПоказу(path.join(джерела,'показ.html')),{__МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'т',__ВІДБИТОК__:'a',
 __ФІД_ПОКАЗУ__:'каталог_brief.xml',__КАТАЛОГ_ПОКАЗУ__:'к',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(джерела)})
 .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/,'<script>window.loadPyodide=null;</script>');
const дом=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://x.test/',beforeParse(w){w.indexedDB=new IDBFactory();w.IDBKeyRange=IDBKeyRange;
 w.fetch=()=>Promise.reject(new Error('нема'));w.scrollTo=()=>{};w.Element.prototype.scrollIntoView=()=>{};}});
const w=дом.window; const стан=w.eval('станТекстуЖінціП');
const лік={}; const відхилені=[];
const слова=w.eval('словаП');
const проза=т=>т.length>=90||/[.!?…]$/.test(т);
for(const ф of файли){ for(const блок of [fs.readFileSync(ф,"utf8")]){ const рядки=блок.split('\n').map(х=>х.trim()).filter(Boolean);
  const свої=new w.Set(); рядки.filter(т=>!проза(т)).forEach(т=>слова(т).forEach(с=>свої.add(с.toLowerCase())));
  for(const т of рядки.filter(проза)){
  const с=стан(т, свої); лік[с]=(лік[с]||0)+1; if(с!=='translated') відхилені.push(с+'\t'+path.relative(process.cwd(),ф).split('/').slice(-3,-2)+'\t'+т.slice(0,400)); } } }
console.log(JSON.stringify(лік)); for(const в of відхилені) console.log(в); process.exit(0);
