/* 4948: ДО/ПІСЛЯ у Chromium на зібраній сторінці, запис Ж26 А/05, без мережі й моделей.
   node проби/оцінка_швидко_4948.js <зібраний html>; потрібні playwright і Chromium. */
const fs = require('fs'), {execFileSync: git} = require('child_process'), {chromium} = require('playwright');
const сцена = '4fe1b840d278ef0404b096656afe381042054db7:аудит/живі_26/А/05_ж1_оціни_образ_6б/';
const читати = шлях => git('git', ['show', шлях], {encoding:'utf8', maxBuffer:16*1024*1024});
const в = JSON.parse(читати(сцена + 'вердикти.txt')).прогони[0].вердикти[0].етапи;
const до = читати('26e5e70ac5d5a464df45e670a257324f51ed4d67:джерела/показ.html').match(/async function мовоюКарткуОцінкиП[\s\S]*?\n}\n/)[0];
(async ()=>{
  const б = await chromium.launch({executablePath:process.env.CHROMIUM || '/usr/bin/chromium', headless:true, args:['--no-sandbox']});
  try{
    const с = await б.newPage({viewport:{width:390,height:844}});
    const html = fs.readFileSync(process.argv[2], 'utf8').replace(/<script[^>]*src="https:[^>]*><\/script>/g, '');
    await с.route('**/*', р => р.request().url() === 'https://probe.invalid/' ? р.fulfill({contentType:'text/html', body:html}) : р.abort());
    await с.goto('https://probe.invalid/#model_mova=replay');
    const вимір = await с.evaluate(async ({в, до})=>{
      const після = мовоюКарткуОцінкиП, виклики = [];
      мовоюП = async (т, де)=>{ const з = в.мова_шару[де.endsWith('.retry') ? 2 : 1];
        виклики.push({де, рядків:Object.keys(т).length, not_run:Object.values(т).filter(x=>/not run/.test(x)).length});
        const тексти = Object.fromEntries(Object.keys(т).map(к=>[к, з.вихід[к] || т[к]]));
        return {тексти, записи:[{де, вхід:т, вихід:тексти}]}; };
      const картка = ()=>JSON.parse(JSON.stringify(в.відповідь.картка));
      eval(до); await мовоюКарткуОцінкиП(картка(), 'review'); const ДО = виклики.splice(0);
      мовоюКарткуОцінкиП = після; const к = картка(); await мовоюКарткуОцінкиП(к, 'review');
      ОЦ.фото = []; ОЦ.етапи = {мова_шару:[]}; ОЦ.результат = {картка:к, сценарій:{}, допит:[]}; малюватиКарткуОцінкиП();
      const ПІСЛЯ = виклики.splice(0), д = document.querySelector('.оц-не-знаю');
      if (!document.querySelector('.оц-відповідь').textContent || !д || д.open) throw Error('card_missing_or_expanded');
      const відкрито = new Promise(р=>д.addEventListener('toggle', р, {once:true}));
      д.open = true; await невідомеОцінкиСловамиП(к, ОЦ.етапи); await відкрито;
      const рядки = [...д.querySelectorAll('.задум > div')].map(x=>x.textContent), розгортання = виклики.splice(0);
      д.open = false; д.open = true; малюватиКарткуОцінкиП(); await невідомеОцінкиСловамиП(к, ОЦ.етапи);
      if (ПІСЛЯ.length !== 1 || ПІСЛЯ.some(x=>x.not_run) || рядки.length !== к.не_знаю.length || виклики.length) throw Error('count_or_repeat');
      if (рядки.some(x=>!x || x === 'Без пояснення словами' || /[a-z_]/i.test(x))) throw Error('missing_text_or_codes_on_screen');
      return {ДО, ПІСЛЯ, розгортання, рядків:рядки.length, записи_відкладеного:ОЦ.етапи.мова_шару.length, повторних:виклики.length};
    }, {в, до});
    console.log(JSON.stringify(вимір, null, 2));
  }finally{ await б.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
