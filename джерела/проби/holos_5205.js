/* Рядок 5205: усі фактичні привʼязки × три браузерні потоки; жодного живого API.
   NODE_PATH=node_modules node проби/holos_5205.js [шаблон-ДО.html] */
const fs=require('fs'), path=require('path'), {JSDOM}=require('jsdom'), {IDBFactory,IDBKeyRange}=require('fake-indexeddb');
const {прочитатиДовідникJSON,підставитиШаблон}=require('../показ_шаблон.js'), дж=path.join(__dirname,'..');
const сирий=fs.readFileSync(process.argv[2]||path.join(дж,'показ.html'),'utf8'), викликів=(сирий.match(/привʼязатиГолос\(\{/g)||[]).length;
class Фейк {
  constructor(){Фейк.останній=this;} start(){} stop(){}
  результат(тип,фін=false){const тексти=тип==='Android'?['перші','перші слова','перші слова далі']:тип==='Chrome'?['перші слова','далі']:['перші слова','далі','далі'];
    this.onresult({results:тексти.map(transcript=>Object.assign([{transcript}],{isFinal:фін})),resultIndex:0});}
}
const html=підставитиШаблон(сирий,{__МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'проба-5205',__ВІДБИТОК__:'abc',
  __ФІД_ПОКАЗУ__:'каталог_brief.xml',__КАТАЛОГ_ПОКАЗУ__:'каталог_стенд.xml',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(дж)})
  .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/,'<script>window.loadPyodide=null;</script>')
  .replace('const кнопка = о.кнопка, поле = о.поле','window.привʼязки.push(о); const кнопка = о.кнопка, поле = о.поле');
const w=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://x.github.io/показ.html',beforeParse(w){
  w.привʼязки=[];w.indexedDB=new IDBFactory();w.IDBKeyRange=IDBKeyRange;w.scrollTo=()=>{};w.Element.prototype.scrollIntoView=()=>{};
  w.SpeechRecognition=Фейк;w.fetch=()=>Promise.reject(new Error('мережі в пробі нема'));}}).window;
const ввести=(о,т)=>{о.поле.value=т;о.поле.dispatchEvent(new w.Event('input',{bubbles:true}));};
const стан=о=>о.поле.id==='чат-поле'?w.eval("($('чат-поле').value||'').trim()"):w.eval(`відповідь(${Number(о.поле.id.split('-').pop())}).коментар`);
const гасити=о=>{if(о.кнопка.getAttribute('aria-pressed')==='true')о.кнопка.click();};
let правок=0,усіх=0,останніх=0,помилок=0,системних=0;
(async()=>{
  await new Promise(р=>setTimeout(р,900));w.eval("П={картки:[{рука:'1',речі:[],знахідки:[],питання:[],мітки:[],підпис:'п',текст:'т'}]}");
  w.document.body.appendChild(w.eval('рендерКартку(0)'));
  if(w.привʼязки.length!==викликів)throw Error(`не покрито виклики: ${w.привʼязки.length}/${викликів}`);
  console.log(`Усі фактичні виклики ${викликів}: ${w.привʼязки.map(о=>о.кнопка.id).join(', ')}`);
  for(const о of w.привʼязки)for(const тип of ['Android','Chrome','iOS'])for(const сц of ['а','б','в','г','д']){
    гасити(о);ввести(о,'');о.кнопка.click();const р=Фейк.останній;р.результат(тип);
    if(['б','в','д'].includes(сц))о.кнопка.click();if(сц==='г')р.onend();if(сц!=='д')ввести(о,'Виправила рукою');
    if(сц==='г'){о.кнопка.click();Фейк.останній.результат(тип,true);р.результат(тип,true);р.onend();р.onerror({error:'network'});}else{р.результат(тип,true);if(сц==='в'||тип==='iOS')р.результат(тип,true);}
    if(тип==='iOS')(сц==='г'?Фейк.останній:р).onend();
    const оч=сц==='д'?'перші слова далі':сц==='г'?'Виправила рукою перші слова далі':'Виправила рукою',добре=о.поле.value===оч&&стан(о)===оч;
    if(сц==='д')останніх+=добре;else{правок+=добре;усіх++;}
    console.log(`${о.кнопка.id} ${тип} (${сц}): поле=${JSON.stringify(о.поле.value)} стан=${JSON.stringify(стан(о))} ${добре?'ЗБЕРЕЖЕНО':'ВТРАЧЕНО'}`);
  }
  for(const о of w.привʼязки){for(const error of ['not-allowed','service-not-allowed','no-speech','aborted','network','audio-capture']){
    гасити(о);ввести(о,'');о.кнопка.click();const р=Фейк.останній;р.результат('Android');р.onerror({error});
    ввести(о,'Правка після помилки');р.результат('Android',true);р.onend();
    const добре=стан(о)==='Правка після помилки'&&о.поле.value===стан(о)&&о.кнопка.getAttribute('aria-pressed')==='false'&&(error==='aborted'||!!о.нота.textContent);
    помилок+=добре;console.log(`${о.кнопка.id} помилка ${error}: ${добре?'ЗБЕРЕЖЕНО':'ВТРАЧЕНО'}; повідомлення=${JSON.stringify(о.нота.textContent)}`);
  }ввести(о,'Системна диктовка');ввести(о,'Виправлена системна диктовка');системних+=стан(о)==='Виправлена системна диктовка'&&о.поле.value===стан(о);}
  console.log(`ПРАВКИ ${правок}/${усіх}; ОСТАННІ СЛОВА ${останніх}/${викликів*3}; ПІСЛЯ ПОМИЛОК ${помилок}/${викликів*6}; СИСТЕМНЕ ВВЕДЕННЯ ${системних}/${викликів}; САМОНАДСИЛАННЯ ${w.eval('ЧАТ_П.length')}`);
  w.close();if(!process.argv[2]&&(правок!==усіх||останніх!==викликів*3||помилок!==викликів*6||системних!==викликів))process.exitCode=1;
})().catch(e=>{console.error(e);w.close();process.exitCode=1;});
