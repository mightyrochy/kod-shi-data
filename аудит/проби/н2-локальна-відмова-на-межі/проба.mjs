import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync, spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const база = '1f75a7298b6f470118c06731f42fb86b5262eb5c';
const до = process.argv.includes('--до');
function джерело(імʼя){
  const шлях = 'джерела/показ/' + імʼя;
  return до ? execFileSync('git', ['show', база + ':' + шлях], {encoding: 'utf8'}) : fs.readFileSync(шлях, 'utf8');
}
function зняти(файл, імена, рядки = []){
  const текст = джерело(файл);
  return [
    ...рядки.map(імʼя => текст.match(new RegExp('^' + імʼя + '[^\\n]*$', 'm'))?.[0]),
    ...імена.map(імʼя => текст.match(new RegExp('^(?:(?:async )?function|class) ' + імʼя + '[ ({][\\s\\S]*?^\\}', 'm'))?.[0]),
  ].map((в, і) => { assert.ok(в, [файл, імена, рядки, і].join(' / ')); return в; }).join('\n');
}
const код = [
  зняти('приміряння.js', ['_фотоБлокиП', 'вмістити_запит_П'], [
    'const СТЕЛЯ_ЗАПИТУ_П = ', 'const ЗАПАС_ЗАПИТУ_П = ', 'const розмірЗапитуП = ', 'const СХОДИ_ФОТО_П = ',
  ]),
  зняти('міст.js', ['підписатиКадри', 'модельП_блоки', 'плануватиВикликП',
    'вмістити_у_вікно_П', '_скоротитиВердиктиП'], [
    'const ЖУРНАЛ_ВИКЛИКІВ_П = ', 'const ЖУРНАЛ_ВИКЛИКІВ_МАКС_П = ', 'let _номерВикликуП = ',
    'const ПОПРАВКА_ТОКЕНІВ_ПОЧАТКОВА_П = ', 'const ПОПРАВКИ_ТОКЕНІВ_П = ', 'const СКОРОЧЕННЯ_ЗА_МЕТОЮ_П = ',
  ]),
  зняти('міст.js', ['оцінкаТокенівП', '_текстиПовідомленьП', '_оцінкаПромптаП', 'токениФотоП',
    'першийОбʼєктП', 'стадіяВикликуП', 'блокиВТекст']),
  зняти('збій_моделі.js', ['ЗбійМоделіП', 'збійМоделіЗВинятку']),
  зняти('ядро.js', ['відповідьМоделіЯдруП', ...(!до ? ['локальнаМежаЯдраП'] : [])]),
].join('\n');

const запуск = new Function('arg', 'режим', код + `
  const МОДЕЛЬ_П='test', МАКС_ТОКЕНІВ_П=4000, МОДЕЛЬ_МОВИ_П='other';
  const базова=Math.ceil(1.1*оцінкаТокенівП(arg.модель.messages[0].content));
  const межа=режим==='вікно' ? базова+4000 : 1000000;
  const НАЛАШТУВАННЯ_РУШІЯ_П={test:{loaded_context_length:межа}};
  ПОПРАВКИ_ТОКЕНІВ_П['test|synthetic-assembly']=1.3;
  let queue=0, transport=0, ОСТАННІ_ЗАГОЛОВКИ_П;
  const МОДЕЛІ_ПРОГОНУ=new Set();
  const задачаПромптаП=()=> 'synthetic-assembly';
  const кредитиЗачиненоП=()=>null, видЗбоюЗПричиниП=()=>null, повторЗбоюМоделіП=()=>null;
  const врахуватиВикликП=()=>{}, записатиКадриП=()=>({дійшло:0});
  function уЧергу(ф) {queue++; return ф();}
  function _дзвінокП(){
    transport++;
    if(режим!=='малий')throw Error('Unexpected transport');
    return new Response(JSON.stringify({content:[{type:'text',text:'offline result'}]}));
  }
  return відповідьМоделіЯдруП(arg).then(adapter=>({adapter,baseline:базова,limit:межа,
    queue,transport,journal:ЖУРНАЛ_ВИКЛИКІВ_П.length}));
`);

for (const режим of ['вікно', 'транспорт', 'малий']){
  const повтор = режим === 'транспорт' ? 100_000 : режим === 'малий' ? 1 : 100;
  const fixture = {вид:'складання', модель:{max_tokens:4000, messages:[
    {content:JSON.stringify({task:{role:'stylist'},case:'слово'.repeat(повтор)})},
  ]}, фото:[]};
  const js = await запуск(fixture, режим);
  if (режим === 'малий'){
    assert.equal(js.adapter.текст,'offline result');
    assert.deepEqual([js.queue,js.transport,js.journal],[1,1,1]);
    console.log(JSON.stringify({режим,js}));
    continue;
  }
  assert.deepEqual([js.queue,js.transport,js.journal],[0,0,0]);
  const py = spawnSync('python3',[fileURLToPath(new URL('провезти.py',import.meta.url))],
    {input:JSON.stringify(js.adapter),encoding:'utf8'});
  assert.equal(py.status,0,py.stderr);
  const протокол = JSON.parse(py.stdout);
  assert.equal(протокол.issued,до ? 2 : 1);
  assert.equal(протокол.terminal.частина,до ? 'модель' : 'запит');
  if (!до){
    const дані = протокол.terminal.дані;
    assert.equal(дані.stage,'складання');
    if(режим==='вікно'){
      assert.equal(протокол.terminal.вид,'вікно_моделі');
      assert.deepEqual([дані.limit_tokens,дані.local_input_tokens_estimate,дані.local_guard_reserved_tokens],[4272,322,4000]);
    }else{
      assert.equal(протокол.terminal.вид,'межа_транспорту');
      assert.equal(дані.transport_limit_utf16_units,396000);
      assert.ok(дані.messages_utf16_units>дані.transport_limit_utf16_units);
    }
  }
  console.log(JSON.stringify({режим,js,протокол}));
}
