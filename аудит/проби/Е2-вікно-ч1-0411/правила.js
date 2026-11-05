/* Функції читаються з робочого дерева; підмінено лише транспорт і полотно. */
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const вхід = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')), функції = вхід.функції;
const контекст = vm.createContext({console, atob, Buffer, assert, записПалітри:вхід.запис});
vm.runInContext(String.raw`
const МОДЕЛЬ_П = 'stylist', МОДЕЛЬ_МОВИ_П = 'language', МАКС_ТОКЕНІВ_П = 4000;
const ПОПРАВКА_ТОКЕНІВ_ПОЧАТКОВА_П = 1.1, ПОПРАВКИ_ТОКЕНІВ_П = {};
const НАЛАШТУВАННЯ_РУШІЯ_П = {stylist:{loaded_context_length:7000}, picture:{loaded_context_length:7000}};
const СКОРОЧЕННЯ_ЗА_МЕТОЮ_П = [_скоротитиВердиктиП], СХОДИ_ФОТО_П = [1024,768,512,384,256];
let останній, транспорту = 0;
function кадр(сторона){
  const б = Buffer.alloc(24); б[0]=137; б.write('PNG',1); б.writeUInt32BE(сторона,16); б.writeUInt32BE(сторона,20);
  return б.toString('base64');
}
async function фотоДоСторониП(ф, сторона){ return {тип:'image/png', дані:кадр(сторона)}; }
async function модельП_блоки(блоки, модель, історія, заголовки, стан, вміщ, вибірка, сигнал, стеля, скорочено){
  const звіт = вмістити_у_вікно_П([{role:'user',content:блоки}], модель, стеля, стадіяВикликуП([{content:блоки}],модель));
  останній = {блоки, модель, історія, заголовки, стан, вміщ, сигнал, скорочено, звіт}; транспорту++;
  return [{type:'text',text:'відповідь'}];
}
async function модельП(промпт,фото,історія,стан,вміщ,вибірка,стеля,сигнал){
  return (await модельП_блоки(блокиЗадачіП(промпт,фото),undefined,історія,undefined,стан,вміщ,вибірка,сигнал,стеля,[]))[0].text;
}
${Object.values(функції).join('\n')}
async function прогін(){
  const історія = {task:{answer:'HELP'}, question:'питання', app:'довідка', state:{screen:'case'},
    conversation:Array.from({length:30},(_,i)=>({from:'her',text:('повідомлення '+i+' ').repeat(50)}))};
  const до = _оцінкаПромптаП([{content:блокиЗадачіП(JSON.stringify(історія))}], 'stylist|інше');
  assert.throws(()=>вмістити_у_вікно_П([{content:блокиЗадачіП(JSON.stringify(історія))}],undefined,undefined,'інше'),/prompt_exceeds_model_window/);
  await модельЗадачіП(JSON.stringify(історія),null,скоротитиДовідкуП);
  let п = JSON.parse(останній.блоки.at(-1).text);
  assert.equal(п.question,історія.question); assert.deepEqual(п.state,історія.state); assert.equal(п.app,історія.app);
  assert.equal(п.conversation.at(-1).text,історія.conversation.at(-1).text);
  assert(п.conversation.length < 30); assert.equal(історія.conversation.length,30);
  console.log('довідка: '+до+' → '+останній.звіт.оцінка_т+' + 4000 ≤ 7000; питання, стан, довідка й остання репліка збережені');

  const палітра = {task:{answer:'PALETTE_CHOICE'}, bases:Array.from({length:100},(_,i)=>({id:'b'+i,
    family:i%2?'neutral':'blue',temperature:'cool',saturation:'soft',notes:'ознака '.repeat(15)})),
    fixed:{base:{id:'b99'}}, schemes:[{scheme:'tonal'},{scheme:'accent'}]};
  await модельЗадачіП(JSON.stringify(палітра),null,скоротитиОсновиП);
  п = JSON.parse(останній.блоки.at(-1).text);
  assert(п.bases.length < 100); assert(п.bases.some(о=>о.id==='b99'));
  assert.equal(new Set(п.bases.map(о=>о.family)).size,2); assert.deepEqual(п.schemes,палітра.schemes);
  console.log('палітра: 100 → '+п.bases.length+'; усі сім’ї, схеми й обрана основа збережені');
  const повтор = '\nReturn JSON, not {a prose answer}.';
  await модельЗадачіП(JSON.stringify(палітра)+повтор,null,скоротитиОсновиП);
  assert(останній.блоки.at(-1).text.endsWith(повтор));
  assert.equal(даніЗадачіП(JSON.stringify({question:'"{}\\"'})+повтор).хвіст,повтор);
  console.log('повтор: JSON скорочено, настанова після нього збережена дослівно');

  const оцінка = {outfit:['p1'], alternatives:['p2','p3'], items:[{id:'p1'},{id:'p2'},{id:'p3'}],
    check:{gate:['p2']}, question:'питання', now:{previous:{answer:'попередня'}}};
  const суд = JSON.stringify(оцінка.check);
  assert.equal(скоротитиОцінкуП(оцінка),'оцінка_альтернативи:1');
  assert.deepEqual(оцінка.alternatives,['p2']); assert.equal(скоротитиОцінкуП(оцінка),null);
  assert.equal(JSON.stringify(оцінка.check),суд); assert.equal(оцінка.now.previous.answer,'попередня');
  assert(оцінка.items.some(р=>р.id==='p1')); console.log('оцінка: захищена альтернатива, вдягнена річ і суд збережені');

  const фото = [{ід:'p1',підпис:'Photo p1',тип:'image/png',дані:кадр(2048)},
    {ід:'p2',підпис:'Photo p2',тип:'image/png',дані:кадр(2048)}];
  const текст = JSON.stringify({question:'питання',items:[{id:'p1'},{id:'p2'}]});
  const вміщ = {}, стан = {}, заголовки = {}, сигнал = {aborted:false};
  await модельЗадачіП(текст,фото,null,'picture',заголовки,стан,вміщ,сигнал);
  assert.equal(останній.блоки.filter(б=>б.type==='image').length,2);
  assert.equal(останній.блоки.filter(б=>б.type==='text').map(б=>б.text).join('|'),'Photo p1:|Photo p2:|'+текст);
  assert(останній.скорочено.some(с=>с.startsWith('фото_роздільність:')));
  assert.equal(останній.сигнал,сигнал); assert.equal(останній.заголовки,заголовки); assert.equal(останній.стан,стан);
  assert.equal(токениФотоП({data:фото[0].дані}).токенів,Math.ceil(2048/28)**2);
  console.log('фото: два кадри й підписи збережені, копії вміщено; модель, заголовки, стан, скасування передані');

  const записані = JSON.parse(записПалітри.промпт);
  const вхідЗапису = _оцінкаПромптаП([{content:блокиЗадачіП(записПалітри.промпт)}],'stylist|інше');
  НАЛАШТУВАННЯ_РУШІЯ_П.stylist.loaded_context_length = вхідЗапису + 4000 - 1;
  await модельЗадачіП(записПалітри.промпт,null,скоротитиОсновиП);
  const післяЗапису = JSON.parse(останній.блоки.at(-1).text);
  const групи = о => [...new Set(о.bases.map(б=>[б.family,б.temperature,б.saturation].join('|')))].sort();
  assert.deepEqual(групи(післяЗапису),групи(записані));
  assert.deepEqual({...післяЗапису,bases:[]},{...записані,bases:[]});
  assert(післяЗапису.bases.length < записані.bases.length);
  console.log('запис б1/01: '+вхідЗапису+' → '+останній.звіт.оцінка_т+'; основи '+записані.bases.length+' → '+післяЗапису.bases.length);
  console.log('джерело: '+записПалітри.джерело);
  НАЛАШТУВАННЯ_РУШІЯ_П.stylist.loaded_context_length = 7000;

  const короткий = JSON.stringify({question:'коротке питання'});
  await модельЗадачіП(короткий,null,скоротитиДовідкуП);
  assert.equal(останній.блоки[0].text,короткий); assert.equal(останній.скорочено.length,0);
  delete НАЛАШТУВАННЯ_РУШІЯ_П.stylist;
  await модельЗадачіП(JSON.stringify(історія),null,скоротитиДовідкуП);
  assert.equal(останній.блоки[0].text,JSON.stringify(історія));
  НАЛАШТУВАННЯ_РУШІЯ_П.stylist={loaded_context_length:4001};
  const було=транспорту;
  await assert.rejects(модельЗадачіП(короткий,null,скоротитиДовідкуП),/prompt_exceeds_model_window/);
  assert.equal(транспорту,було);
  console.log('короткий запит і режим без вікна незмінні; неподільний залишок відхилено до транспорту');
}
прогін().catch(е=>{console.error(е);process.exitCode=1});
`,контекст);
