/* Chromium 390×844: той самий контрольований збій ДО/ПІСЛЯ на справжньому показі. */
const fs = require('fs'), path = require('path'), {execFileSync} = require('child_process');
process.env.PYTHONIOENCODING = 'utf-8'; process.env.PYTHONUTF8 = '1';
const корінь = path.resolve(process.argv[2]), тека = path.resolve(process.argv[3] || __dirname);
const джерела = path.join(корінь, 'джерела');
const {chromium} = require(path.join(джерела, 'node_modules/playwright'));
const {зібратиШаблонПоказу, підставитиШаблон, прочитатиДовідникJSON} = require(path.join(джерела, 'показ_шаблон.js'));
const вихідний = path.join(корінь, 'аудит/проби/ремонт_шар.js');
const початок = fs.readFileSync(вихідний, 'utf8').split('(async () => {')[0];
const {міст, повідомлення} = new Function('require', '__dirname', 'process',
  початок + '\nreturn {міст, повідомлення};')(require, path.dirname(вихідний), {argv: []});
async function main(){
  fs.mkdirSync(тека, {recursive:true});
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(джерела, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: '1974-6c944ef7', __ВІДБИТОК__: '1974-6c944ef7',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'проба',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(джерела)});
  const поточний = fs.readFileSync(path.join(джерела, 'показ/мовний_шар.js'), 'utf8');
  const попередній = execFileSync('git', ['show', '2c107632bdb24ac170c715ed181499abe1dbc67c:джерела/показ/мовний_шар.js'],
    {cwd:корінь, encoding:'utf8'});
  const браузер = await chromium.launch({headless:true, ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH}: {})});
  const результати = [];
  try {
    for (const до of [true, false]){
      const стор = await браузер.newPage({viewport:{width:390,height:844}, deviceScaleFactor:1});
      const помилки = []; стор.on('pageerror', е => помилки.push(е.stack || String(е)));
      await стор.exposeFunction('містПеревірки', міст);
      await стор.route('**/*', р => р.request().url() === 'http://offline.local/'
        ? р.fulfill({contentType:'text/html', body: до ? html.replace(поточний, () => попередній) : html}) : р.abort());
      await стор.goto('http://offline.local/#model_mova=запис');
      try { await стор.waitForFunction(() => !!document.getElementById('сцн-новий').onclick); }
      catch(е){throw Error(String(е) + '\n' + помилки.join('\n'));}
      const факти = await стор.evaluate(async питання => {
        містП = async (_, д) => window.містПеревірки(д);
        модельМовиП = async () => '{}';
        const к = {рука:'1', опис:'Світлий верх і темні штани для робочого дня.',
          речі:[{id:'проба-1', слот:'верх', назва:'Світла блуза', ціна:1500},
            {id:'проба-2', слот:'низ', назва:'Темні штани', ціна:2100}], питання,
          знахідки:[], мітки:[], мова:[], свідомі:[], етапи:{виклики:[]}};
        await питаннямиП(к, 'hand_1');
        П = {картки:[к], профіль:'Проба', випадок:'Робочий день', в:'ПОКАЗ-V1'};
        document.getElementById('картки').replaceChildren(рендерКартку(0));
        режим('образи');
        return {текстів: (к.питання_жінці || []).length,
          стани: к.питання.map(п => п.стан_перекладу || null),
          підпис: document.querySelector('.питання-коду summary')?.textContent || null};
      }, [повідомлення('а'),повідомлення('б'),повідомлення('в')].map(п => ({повідомлення:п})));
      await стор.locator('#к-0').scrollIntoViewIfNeeded();
      await стор.screenshot({path:path.join(тека, до ? 'до.png' : 'після.png')});
      if(!до){
        await стор.locator('.питання-коду summary').click();
        await стор.locator('.питання-коду').evaluate(е => е.scrollIntoView({block:'start'}));
        await стор.screenshot({path:path.join(тека,'після-розгорнуто.png')});
      }
      результати.push({стан:до ? 'ДО' : 'ПІСЛЯ', ...факти, помилки});
      await стор.close();
    }
  } finally {await браузер.close();}
  fs.writeFileSync(path.join(тека,'браузер.json'), JSON.stringify(результати,null,2));
  console.log(JSON.stringify(результати,null,2));
}
main().catch(е => {console.error(е);process.exitCode=1;});
