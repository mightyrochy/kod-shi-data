/* Незалежна прицільна проба: виконує координатор голови PR, підміняє лише відповіді рук і транспорту. */
const fs = require('fs'), path = require('path'), Module = require('module');
const root = process.argv[2], source = path.join(root, 'джерела');
process.argv = process.argv.slice(0, 2);
const filename = path.join(source, 'тест_показу.js');
const code = fs.readFileSync(filename, 'utf8');
const helper = new Module(filename, module);
helper.filename = filename; helper.paths = Module._nodeModulePaths(source);
helper._compile(code.slice(0, code.indexOf('\n(async () => {')) + '\nmodule.exports={сторінка,чекатиСтарт,чекатиНа};', filename);
const {сторінка,чекатиСтарт,чекатиНа} = helper.exports;
async function scene(mode) {
  const {w,d,помилки} = сторінка({url:'https://mightyrochy.github.io/kod-shi-data/показ.html#міст=http://localhost:8787&т=probe&модель_мови=нема'});
  await чекатиСтарт(w);
  w.eval(`чогоБракує = () => []; немаВизначальнихП = () => false;
    ПАСПОРТ_П = {джерело:'модель', ошатність:[3,5], нагода:'робота', вето:{}}; ВИПАДОК_ЗМІНЕНО_П=false;
    стилісткаОбираєП = async () => null;
    вхідМостаП = () => ({імʼя:'Перевірка',сід:3});
    містП = async ім => ім === 'запити' ? {руки:{'1':'"outfits":','2':'"outfits":','3':'3','4':'4'},правила_рук:{},пул_речей:1} : {};
    перемішатиП = () => ['1','2','3','4'];
    window.__gate = new Promise(r => window.__release = r);
    window.__oneHand = async поз => { if (поз) await window.__gate;
      const к = {рука:String(поз+1), текст:'Сукня для роботи.', речі:[{id:'probe-'+поз,назва:'Сукня',ціна:1000,слот:'сукня'}],
        мітки:[],знахідки:[],збирання:{позиція:поз}, етапи:{}};
      if (поз === 3 && window.__fail) {к.збій = {вид:'probe_failure'}; к.речі=[];}
      ЗБ.картки[поз]=к; ЗБ.готові_мс[поз]=Date.now()-ЗБ.почато;
    };
    window.__fail = true;`);
  const coordinator = fs.readFileSync(path.join(source,'показ','збирання_образів.js'),'utf8');
  w.eval('window.__coordinator=(function(однаРука){'+coordinator+'\nreturn зібратиОбразиП;})(window.__oneHand);window.__build=window.__coordinator();');
  await чекатиНа(() => w.eval("!!П && !!ЗБ.руки_йдуть && П.картки.length===1"),'рання картка не зʼявилась');
  if (mode === 'бібліотека') {
    await w.eval('оновитиБібліотеку()');
    const index = w.eval('БІБЛІОТЕКА_П.плитки.findIndex(x=>String(x.ід).startsWith(П.прогін+"#"))');
    if (index < 0) throw new Error('ранній запис відсутній у бібліотеці');
    await w.eval('відкритиОбразБібліотекиП('+index+')');
  }
  w.eval(`window.__before = П; window.__card = П.картки[0];
    містП = async ім => ім === 'від_моделі' ? {заміна:{готово:true,річ:{id:'замінена',слот:'сукня'},ід:['замінена'],вердикт:{}}}
      : ім === 'показ' ? [{id:'замінена',назва:'Обрана сукня',слот:'сукня',ціна:900}] : {};
    мовоюКарткуП = async () => {};
    window.__replace = замінитиРічП(0,'probe-0');`);
  await w.__replace;
  if (w.eval("П.картки[0].речі[0].id") !== 'замінена') throw new Error('штатна заміна не застосувалася');
  w.eval(`window.__node = document.getElementById('к-0'); відповідь(0).коментар='мої слова';`);
  if (mode === 'інший') w.eval(`П={в:'ПОКАЗ-V1',прогін:'інший-прогін',картки:[{рука:'1',текст:'Інший образ.',речі:[],мітки:[],знахідки:[]}]}; рендер();`);
  const before = w.eval("JSON.stringify({прогін:П.прогін,речі:П.картки[0].речі.map(x=>x.id),підпис:document.getElementById('обр-підпис').textContent})");
  w.__release(); await w.__build;
  await w.eval('оновитиБібліотеку()');
  const result = await w.eval(`(async()=>{const db=await дб(); const records=await tx(db,'вердикти','readonly',s=>s.getAll());
    const builds=await tx(db,'образи','readonly',s=>s.getAll());
    return {готово:ЗБ.готово,успіх:ЗБ.успіх,прогін:П.прогін,картки:П.картки.map(x=>x.рука),
      речі:П.картки[0].речі.map(x=>x.id),той_самий_П:П===window.__before,та_сама_картка:П.картки[0]===window.__card,
      той_самий_DOM:document.getElementById('к-0')===window.__node,слова:відповідь(0).коментар,
      підпис:document.getElementById('обр-підпис').textContent,
      бібліотека:builds.map(x=>({прогін:x.прогін,руки:x.П.картки.map(k=>k.рука),речі:x.П.картки[0].речі.map(r=>r.id)})),
      збої:records.filter(x=>x.рука_впала).map(x=>({прогін:x.прогін,рука:x.рука,авто:x.запис_автоматичний})),
      діагноз:ЗБ.діагноз};})()`);
  console.log(JSON.stringify({сцена:mode,ДО:JSON.parse(before),ПІСЛЯ:result,помилки},null,2));
  w.close();
}
(async()=>{for(const mode of ['картка','бібліотека','інший'])await scene(mode);})().catch(e=>{console.error(e);process.exitCode=1});
