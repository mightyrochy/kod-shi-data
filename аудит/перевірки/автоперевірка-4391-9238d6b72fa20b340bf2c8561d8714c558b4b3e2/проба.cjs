/* Прицільна проба автоперевірки #4391 (голова 9238d6b72fa20b340bf2c8561d8714c558b4b3e2):
   1) 16733 — відкритий екран «Усі образи» (`режим('бібліотека')`) через шов рук 2–4: після шва на екрані
      лишається 1 застаріла плитка, а клік по ній (`відкритиОбразБібліотекиП`) відкочує `П`, екран і IndexedDB
      бібліотеки з 4 рук назад до 1 руки (втрачаючи руки 2–4 і `час_збору`).
   2) 16734 — гонка на `await записатиЗбоїРукП(запис)` у шві `збирання_образів.js`: перемикання `П` на інший
      прогін під час очікування автозапису впалої руки залишає застаріле `екранПішов === false`, і `дописатиОбрази`
      зберігає чужий прогін, не зберігаючи 4-руковий запис свого прогону в бібліотеку.
   Запуск: NODE_PATH=джерела/node_modules node аудит/перевірки/автоперевірка-4391-9238d6b72fa20b340bf2c8561d8714c558b4b3e2/проба.cjs <корінь> */
const fs = require('fs'), path = require('path'), Module = require('module');
const root = process.argv[2], source = path.join(root, 'джерела');
process.argv = process.argv.slice(0, 2);
const filename = path.join(source, 'тест_показу.js');
const code = fs.readFileSync(filename, 'utf8');
const helper = new Module(filename, module);
helper.filename = filename; helper.paths = Module._nodeModulePaths(source);
helper._compile(code.slice(0, code.indexOf('\n(async () => {')) + '\nmodule.exports={сторінка,чекатиСтарт,чекатиНа};', filename);
const {сторінка, чекатиСтарт, чекатиНа} = helper.exports;

async function startBuild(extraSetup = ''){
  const {w, помилки} = сторінка({url:'https://mightyrochy.github.io/kod-shi-data/показ.html#міст=http://localhost:8787&т=probe&модель_мови=нема'});
  await чекатиСтарт(w);
  w.eval(`чогоБракує = () => []; немаВизначальнихП = () => false;
    ПАСПОРТ_П = {джерело:'модель', ошатність:[3,5], нагода:'робота', вето:{}}; ВИПАДОК_ЗМІНЕНО_П=false;
    стилісткаОбираєП = async () => null; вхідМостаП = () => ({імʼя:'Перевірка',сід:3});
    містП = async ім => ім === 'запити' ? {руки:{'1':'"outfits":','2':'"outfits":','3':'3','4':'4'},правила_рук:{},пул_речей:1} : {};
    перемішатиП = () => ['1','2','3','4'];
    window.__gate = new Promise(r => window.__release = r);
    ${extraSetup}
    window.__oneHand = async поз => { if (поз) await window.__gate;
      const к = {рука:String(поз+1), текст:'Сукня для роботи.', речі:[{id:'probe-'+поз,назва:'Початкова сукня',ціна:1000,слот:'сукня'}],
        мітки:[],знахідки:[],збирання:{позиція:поз}, етапи:{}};
      if (поз === 3) { к.збій = {вид:'probe_failure'}; к.речі=[]; }
      ЗБ.картки[поз]=к; ЗБ.готові_мс[поз]=Date.now()-ЗБ.почато; };`);
  const coordinator = fs.readFileSync(path.join(source,'показ','збирання_образів.js'),'utf8');
  w.eval('window.__build=(function(однаРука){'+coordinator+'\nreturn зібратиОбразиП;})(window.__oneHand)();');
  await чекатиНа(() => w.eval("!!П && П.картки.length===1 && !!ЗБ && !ЗБ.готово"), 'рання картка не зʼявилась');
  w.eval(`window.__прогін = П.прогін;`);
  return {w, помилки};
}

async function main(){
  // Сцена 1 (16733): відкриті «Усі образи» через шов, потім клік по плитці свого прогону
  {
    const {w, помилки} = await startBuild();
    await w.eval(`режим('бібліотека');`);
    await чекатиНа(() => w.eval("БІБЛІОТЕКА_П.плитки.some(x=>String(x.ід).startsWith(window.__прогін+'#'))"), 'бібліотека не прочиталась');
    w.__release();
    await чекатиНа(() => w.eval("ЗБ.готово"), 'шов не скінчився');
    await w.eval('ЗАПИС_ОБРАЗУ_П');
    const доКліку = await w.eval(`(async()=>{const db=await дб(); const о=await tx(db,'образи','readonly',s=>s.getAll());
      const с=о.find(x=>x.прогін===window.__прогін);
      return {режим:Екран.стан.режим, плиток_в_DOM:document.querySelectorAll('#біб-список .біб-образ').length,
        П_руки:П.картки.map(x=>x.рука), біб_руки:с?с.П.картки.map(x=>x.рука):null, час_збору:!!(с&&с.П.час_збору)};})()`);
    const н = w.eval("БІБЛІОТЕКА_П.плитки.findIndex(x=>String(x.ід).startsWith(window.__прогін+'#'))");
    w.eval(`відкритиОбразБібліотекиП(${н})`);
    await w.eval('ЗАПИС_ОБРАЗУ_П');
    const післяКліку = await w.eval(`(async()=>{const db=await дб(); const о=await tx(db,'образи','readonly',s=>s.getAll());
      const с=о.find(x=>x.прогін===window.__прогін);
      return {режим:Екран.стан.режим, DOM_карток:document.querySelectorAll('#картки > .картка').length,
        П_руки:П.картки.map(x=>x.рука), біб_руки:с?с.П.картки.map(x=>x.рука):null, час_збору:!!(с&&с.П.час_збору),
        підпис:document.getElementById('обр-підпис').textContent};})()`);
    console.log(JSON.stringify({сцена:'16733_відкрита_бібліотека_через_шов', доКліку, післяКліку, помилки:помилки.map(String)}));
    w.close();
  }

  // Сцена 2 (16734): перехід на інший прогін під час await записатиЗбоїРукП(запис)
  {
    const {w, помилки} = await startBuild(`
      const __origZ = записатиЗбоїРукП;
      записатиЗбоїРукП = async п => { await new Promise(r => { window.__inZboi = r; }); return __origZ(п); };`);
    w.__release();
    await чекатиНа(() => !!w.__inZboi, 'не зайшло в записатиЗбоїРукП');
    w.eval(`П={в:'ПОКАЗ-V1',прогін:'інший-прогін',картки:[{рука:'1',текст:'Інший образ.',речі:[],мітки:[],знахідки:[]}]}; рендер();`);
    w.__inZboi();
    await чекатиНа(() => w.eval("ЗБ.готово"), 'шов не скінчився');
    await w.eval('ЗАПИС_ОБРАЗУ_П');
    const після = await w.eval(`(async()=>{const db=await дб(); const о=await tx(db,'образи','readonly',s=>s.getAll());
      const с=о.find(x=>x.прогін===window.__прогін);
      return {П_прогін:П.прогін, П_руки:П.картки.map(x=>x.рука),
        біб_руки_свого:с?с.П.картки.map(x=>x.рука):null, біб_час_збору_свого:!!(с&&с.П.час_збору),
        діагноз:ЗБ.діагноз.filter(д=>/late_hands/.test(д))};})()`);
    console.log(JSON.stringify({сцена:'16734_гонка_записатиЗбоїРукП', після, помилки:помилки.map(String)}));
    w.close();
  }
  process.exit(0);
}
main().catch(e => { console.error(e); process.exit(1); });
