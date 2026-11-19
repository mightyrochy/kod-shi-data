/* Незалежна проба шва й журналу. Аргумент — тека джерел перевіреної голови. */
const fs = require('fs'), path = require('path'), Module = require('module');
const src = path.resolve(process.argv[2]);
const test = path.join(src, 'тест_показу.js');
const helper = new Module(test, module);
helper.filename = test; helper.paths = Module._nodeModulePaths(src);
const argv = process.argv; process.argv = argv.slice(0, 2);
helper._compile(fs.readFileSync(test, 'utf8').split('\n(async () => {')[0]
  + '\nmodule.exports = {відкритиПакет, чекатиНа};', test);
process.argv = argv;
const {відкритиПакет, чекатиНа} = helper.exports;
const card = () => ({рука:'1', текст:'Образ.', речі:[{id:'ж-00003@gepur.com', назва:'Сукня', слот:'сукня', ціна:100}], мітки:[], знахідки:[]});
const packet = () => ({в:'ПОКАЗ-V1', збірка:'проба', каталог:'каталог', профіль:'Оля', розклад:'1234', прогін:'проба-4350',
  знімок:{в:'ЗНІМОК-ПРОГОНУ-V1', вхід:{}}, картки:[card()]});
const coord = fs.readFileSync(path.join(src, 'показ/збирання_образів.js'), 'utf8');
const compose = coord.slice(coord.indexOf('const складатиП = () => {'), coord.indexOf('/* збирання руки однією функцією'));
const seal = coord.slice(coord.indexOf('const екранНаЦьомуПрогоні'), coord.indexOf('const секунд = Math.round'));
const finish = `(async () => {const ранній = П, ід_прогону = П.прогін, вх = {}, пул = null;
  ${compose} ${seal} ЗБ.руки_йдуть = null; дописатиОбрази(стоїть); })()`;
async function fixture(){
  const f = await відкритиПакет(packet());
  await чекатиНа(() => !!f.d.getElementById('к-0'), 'картка');
  f.w.eval(`ЗБ = {картки:П.картки.concat([{рука:'2',текст:'Друга.',речі:[],мітки:[],знахідки:[]}]),
    діагноз:[],ключ:[1,2,3,4],стадії:[],етап:[],готові_мс:[],руки_йдуть:П.прогін};`);
  return f;
}
async function replacement(withSeal){
  const {w,d,дом} = await fixture();
  w.eval(`window.__oldP = П; window.__oldNode = document.getElementById('к-0');
    window.__release = null; window.__entered = false;
    містП = async (ім, дані) => { if (ім === 'від_моделі') {
      window.__entered = true; await new Promise(r => window.__release = r);
      return {заміна:{готово:true,річ:{id:'нова',слот:'сукня'},ід:['нова'],вердикт:{}}};
    } if (ім === 'показ') return [{id:'нова',слот:'сукня',назва:'Нова сукня'}]; return {}; };
    мовоюКарткуП = async () => {}; вхідМостаП = () => ({});
    window.__replace = замінитиРічП(0, 'ж-00003@gepur.com');`);
  await чекатиНа(() => w.__entered, 'заміна почалася');
  if (withSeal) await w.eval(finish);
  w.__release(); await w.__replace;
  console.log((withSeal ? 'ЗАМІНА ПІСЛЯ ШВА ' : 'ЗАМІНА БЕЗ ШВА ') + w.eval(`JSON.stringify({той_самий_ід:П.прогін === window.__oldP.прогін,
    той_самий_обєкт:П === window.__oldP, той_самий_DOM:document.getElementById('к-0') === window.__oldNode,
    річ:П.картки[0].речі[0].id, заміна_іде:показЗаміниП(0).іде})`));
  дом.window.close();
}
(async () => {
  await replacement(false);
  await replacement(true);
  const f2 = await fixture();
  await f2.w.eval(`(async () => { window.__own = {...П, картки:[...П.картки,
    {рука:'2',речі:[],мітки:[],знахідки:[]}, {рука:'3',речі:[],мітки:[],знахідки:[]},
    {рука:'4',збій:'наведений збій',речі:[],мітки:[],знахідки:[]}]};
    П = {...П,прогін:'інший-прогін',картки:[П.картки[0]]};
    await записатиЗбоїРукП(window.__own);
    ПРОГІН_ІНШИЙ_П = window.__own; await зберегтиОбраз(); })()`);
  console.log('ЖУРНАЛ І БІБЛІОТЕКА ' + await f2.w.eval(`(async () => JSON.stringify({екран:П.прогін,
    записи:(await усіВердикти()).map(x=>({прогін:x.прогін,рука:x.рука,позиція:x.позиція})),
    образи:(await усіОбрази()).map(x=>({прогін:x.прогін,руки:x.П.картки.map(k=>k.рука)})),
    діагноз:ЗБ.діагноз}))()`));
  f2.дом.window.close();
})().catch(e => {console.error(e);process.exitCode=1;});
