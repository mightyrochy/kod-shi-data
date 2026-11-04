/* Спільна пропозиція: один текст і всі її запасні речі, без виконання моделі. */
const {JSDOM} = require('jsdom'), fs = require('fs'), path = require('path'), assert = require('assert');
const {execFileSync} = require('child_process');
const джерела = path.resolve(__dirname, '..');
function показ(код){
  const д = new JSDOM('<!doctype html><meta charset="utf-8"><body><h2>Що змінити</h2>', {runScripts: 'outside-only'});
  const в = д.window;
  в.ел = (т, к, с)=>{ const е = в.document.createElement(т); if (к) е.className = к; if (с) е.textContent = с; return е; };
  в.елЖінціП = в.ел; в.своїЕкрануП = ()=>({}); в.урлФотоП = ф=>ф.url; в.кадрРечіУрлП = async ()=>null;
  в.ОЦ = {фото: ['ф5', 'ф6'].map((ід, н)=>({ід, url: 'data:image/svg+xml,' + encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="80" height="100"><path fill="${н ? '#94734f' : '#d8cbb5'}" d="M15 10h50v80H15z"/></svg>`)}))};
  в.eval(код.slice(код.indexOf('function рядокЗміниП('), код.indexOf('function вердиктОцінкиП(')));
  const складові = [{ціль: 'ф1', нова: 'ф5'}, {ціль: 'ф2', нова: 'ф6'}];
  const зміна = {звідки: 'own', ціль: 'ф1', нова: 'ф5', складові};
  в.document.body.appendChild(в.рядокЗміниП({текст: 'Кремовий гольф і коричнева косуха — разом.', зміна},
    {суд: {речі: ['ф5', 'ф6'].map(ід=>({ід, фото: ід}))}}));
  return д;
}
async function головна(){
  const шлях = 'джерела/показ/розмова_з_фото.js';
  const до = показ(execFileSync('git', ['show', 'b694ac2d2469b4191978e4e716ac2a912715dd58:' + шлях], {cwd: джерела, encoding: 'utf8'}));
  const після = показ(fs.readFileSync(path.join(джерела, 'показ/розмова_з_фото.js'), 'utf8'));
  assert.equal(до.window.document.images.length, 1); assert.equal(після.window.document.images.length, 2);
  assert.equal(після.window.document.querySelectorAll('.оц-спільна-зміна > .назва').length, 1);
  assert.notEqual(після.window.document.images[0].src, після.window.document.images[1].src);
  if (process.argv[2]){
    const вихід = path.resolve(process.argv[2]);
    assert(вихід.startsWith(path.resolve(джерела, '../../tmp') + path.sep));
    const {chromium} = require('playwright');
    const браузер = await chromium.launch({channel: 'chrome', headless: true});
    try { const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
      const стиль = fs.readFileSync(path.join(джерела, 'показ.html'), 'utf8').match(/<style[^>]*>([\s\S]*?)<\/style>/)[1];
      for (const [імя, д] of [['ДО', до], ['ПІСЛЯ', після]]) { await сторінка.setContent(д.serialize());
        await сторінка.addStyleTag({content: стиль}); await сторінка.screenshot({path: path.join(вихід, імя + '.png')}); }
    } finally { await браузер.close(); }
  }
  console.log('Спільна заміна: мініатюр 1 → 2; текст один; viewport 390×844');
  до.window.close(); після.window.close();
}
if (require.main === module) головна().catch(е=>{ console.error(е); process.exitCode = 1; });
