/* Проба виконавця (не код продукту) до знахідки дошки: рука 3 кидає виняток ПОЗА своїм `try` (крок після складання,
   як `збиранняКарткиРуки` / `стадіяМовногоШару`), коли картка руки 1 уже на екрані. Що бачить жінка: режим, картки,
   запис бібліотеки й журнал прогону; руки 2 і 4 доходять після винятку.
   Координатор — `збирання_образів.js` дерева <корінь>, як є; підмінено лише відповіді рук і транспорт заміни.
   Основа — `проба.cjs` автоперевірки #4350 ba43ce3e (умову «рання картка показана» взято з `П`, а не з `ЗБ.руки_йдуть`).
   Запуск: NODE_PATH=джерела/node_modules node проба_виняток.cjs <корінь дерева> */
const fs = require('fs'), path = require('path'), Module = require('module');
const root = process.argv[2], source = path.join(root, 'джерела');
process.argv = process.argv.slice(0, 2);
const filename = path.join(source, 'тест_показу.js');
const code = fs.readFileSync(filename, 'utf8');
const helper = new Module(filename, module);
helper.filename = filename; helper.paths = Module._nodeModulePaths(source);
helper._compile(code.slice(0, code.indexOf('\n(async () => {')) + '\nmodule.exports={сторінка,чекатиСтарт,чекатиНа};', filename);
const {сторінка, чекатиСтарт, чекатиНа} = helper.exports;
const ЗАМІНА = `містП = async ім => {
    if (ім === 'від_моделі'){ if (window.__тримати) await new Promise(р => window.__відпустити = р);
      return {заміна:{готово:true,річ:{id:'замінена',слот:'сукня'},ід:['замінена'],вердикт:{}}}; }
    return ім === 'показ' ? [{id:'замінена',назва:'Обрана сукня після заміни',слот:'сукня',ціна:900}] : {}; };
  мовоюКарткуП = async () => {};`;
async function сцена(){
  const {w, d, помилки} = сторінка({url:'https://mightyrochy.github.io/kod-shi-data/показ.html#міст=http://localhost:8787&т=probe&модель_мови=нема'});
  await чекатиСтарт(w);
  w.eval(`чогоБракує = () => []; немаВизначальнихП = () => false;
    ПАСПОРТ_П = {джерело:'модель', ошатність:[3,5], нагода:'робота', вето:{}}; ВИПАДОК_ЗМІНЕНО_П=false;
    стилісткаОбираєП = async () => null; вхідМостаП = () => ({імʼя:'Перевірка',сід:3});
    містП = async ім => ім === 'запити' ? {руки:{'1':'"outfits":','2':'"outfits":','3':'3','4':'4'},правила_рук:{},пул_речей:1} : {};
    перемішатиП = () => ['1','2','3','4'];
    window.__gate = new Promise(r => window.__release = r);
    window.__oneHand = async поз => { if (поз) await window.__gate;
      const к = {рука:String(поз+1), текст:'Сукня для роботи.', речі:[{id:'probe-'+поз,назва:'Початкова сукня',ціна:1000,слот:'сукня'}],
        мітки:[],знахідки:[],збирання:{позиція:поз}, етапи:{}};
      if (поз === 2) throw new Error('probe_hand_3_threw_outside_try');
      ЗБ.картки[поз]=к; ЗБ.готові_мс[поз]=Date.now()-ЗБ.почато; };`);
  const coordinator = fs.readFileSync(path.join(source,'показ','збирання_образів.js'),'utf8');
  w.eval('window.__build=(function(однаРука){'+coordinator+'\nreturn зібратиОбразиП;})(window.__oneHand)();');
  await чекатиНа(() => w.eval("!!П && П.картки.length===1 && !!ЗБ && !ЗБ.готово"), 'рання картка не зʼявилась');
  w.eval(`window.__прогін = П.прогін; window.__сценарій = JSON.stringify(П.сценарій);`);
  const підписи = [w.eval("document.getElementById('обр-підпис').textContent")];
  const відкритиЗБібліотеки = async () => { await w.eval('оновитиБібліотеку()');
    const н = w.eval('БІБЛІОТЕКА_П.плитки.findIndex(x=>String(x.ід).startsWith(window.__прогін+"#"))');
    if (н < 0) throw new Error('ранній запис відсутній у бібліотеці'); w.eval('відкритиОбразБібліотекиП('+н+')'); };
  w.eval(`window.__вузол = document.getElementById('к-0');`);
  const ДО = w.eval(`JSON.stringify({режим:Екран.стан.режим, П_руки:П.картки.map(x=>x.рука)})`);
  w.__release();
  await чекатиНа(() => w.eval("!ЗБИРАННЯ_ЗАЙНЯТО_П"), 'збирання не скінчилось');
  await new Promise(р => setTimeout(р, 300));   /* руки 2 і 4 доходять після винятку */
  await w.eval('ЗАПИС_ОБРАЗУ_П'); await w.eval('оновитиБібліотеку()');
  const ПІСЛЯ = await w.eval(`(async()=>{const db=await дб(); const вердикти=await tx(db,'вердикти','readonly',s=>s.getAll());
    const образи=await tx(db,'образи','readonly',s=>s.getAll()); const свій=образи.find(x=>x.прогін===window.__прогін);
    return {готово:ЗБ.готово, успіх:!!ЗБ.успіх, режим:Екран.стан.режим, прогін_на_екрані:П.прогін===window.__прогін,
      П_руки:П.картки.map(x=>x.рука), ЗБ_руки:ЗБ.картки.filter(Boolean).map(x=>x.рука),
      картка_руки_1_в_DOM: !!document.getElementById('к-0'),
      бібліотека_руки: свій?свій.П.картки.map(k=>k.рука):null,
      журнал_рук: вердикти.filter(x=>x.прогін===window.__прогін).map(x=>x.рука),
      відмова: (document.getElementById('зб-відмова')||{}).textContent||null,
      діагноз: ЗБ.діагноз.filter(д=>/build ·|probe_hand/.test(д)).map(д=>д.slice(0,120))};})()`);
  w.close();
  return {ДО: JSON.parse(ДО), ПІСЛЯ, помилки: помилки.map(String).map(x=>x.slice(0,160))};
}
(async () => {
  try{ console.log(JSON.stringify(await сцена(), null, 1)); }
  catch(e){ console.log(JSON.stringify({ВИНЯТОК: String(e && e.stack || e).slice(0, 600)})); }
})();
