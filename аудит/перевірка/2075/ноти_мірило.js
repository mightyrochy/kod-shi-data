/* Власна проба передумови тесту нот: лічильник викликів не є поколінням входу. */
const fs=require('fs'),path=require('path'),Module=require('module');
const root=path.resolve(__dirname,'../../../джерела');
const source=fs.readFileSync(path.join(root,'тест_показу.js'),'utf8');
const prefix=source.slice(0,source.indexOf('\n(async () => {'));
const body=String.raw`
(async()=>{
 const results=[];
 for(const bridgeDelay of [0,50]){
  const {w,d}=сторінка({url:'https://mightyrochy.github.io/kod-shi-data/показ.html'});
  await чекатиСтарт(w);
  let calls=0;w._trace=[];
  w._заглушкаТранспорту=async(ім,рядок)=>{
   const x=JSON.parse(рядок);await new Promise(r=>setTimeout(r,++calls===1?bridgeDelay:0));
   return JSON.stringify({основи:{нейтралі:[],кольори:[],інші:[]},гілки:[],вибір_кольору:{},мітка:x.мітка,
     гейт:{утримано:[],можна_стверджувати:[]},осі_джерело:'самозвіт',осі_коди:{value:'light',chroma:'soft',hue:'warm'}});
  };
  w.eval("транспортМостуП=(...a)=>window._заглушкаТранспорту(...a);КОЛІР={шкіра:'#deb295',волосся:'#f1dbaa',очі:'#759087'};"
   +"let __input='старий',__counter=0;вхідПалітри=()=>({мітка:__input});window.__input=x=>{__input=x};"
   +"повідомленнямП=async()=>{const n=++__counter,input=ПАЛІТРА.мітка;window._trace.push({n,input});"
   +"await new Promise(r=>setTimeout(r,n===1?120:5));return {тексти:{'пал-нота':'нота-'+input+'-'+n},записи:[]}};");
  const first=w.eval('оновитиПалітруП()');
  await new Promise(r=>setTimeout(r,30));w.__input('новий');
  const second=w.eval('оновитиПалітруП()');await Promise.all([first,second]);
  const text=d.getElementById('пал-нота').textContent;
  if(!text.startsWith('нота-новий-'))throw new Error(text);
  results.push({bridgeDelay,trace:w._trace,text,правильний_останній_вхід:true,лічильник_2:text.endsWith('-2')});
  w.close();
 }
 console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});`;
const virtual=path.join(root,'перевірка-2075-ноти.js');
const m=new Module(virtual,module);m.filename=virtual;m.paths=Module._nodeModulePaths(root);m._compile(prefix+body,virtual);
