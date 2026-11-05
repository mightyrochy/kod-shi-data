/* Знімає справжній діалог підтвердження в шаблоні показу без мережі та моделі.
   Запуск із кореня репозиторію, залежності — через NODE_PATH. */
const fs = require('fs');
const path = require('path');
const {execFileSync} = require('child_process');
const {chromium} = require('playwright');
const джерела = path.join(process.cwd(), 'джерела');
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(джерела, 'показ_шаблон.js'));
const довідник = прочитатиДовідникJSON(джерела);
const база = 'fa8e5c305c5e6f2ec3faf8f1b5841760ce6b4bed';

/* Підміняє лише два змінені модулі для знімка ДО; решта джерел спільна. */
function шаблон(до){
  const читати = fs.readFileSync;
  const старі = new Map(до ? ['мовний_шар.js', 'міст.js'].map(ім => [
    path.join(джерела, 'показ', ім),
    execFileSync('git', ['show', база + ':джерела/показ/' + ім], {encoding: 'utf8'}),
  ]) : []);
  fs.readFileSync = function(файл){
    if (typeof файл === 'string' && старі.has(path.resolve(файл))) return старі.get(path.resolve(файл));
    return читати.apply(this, arguments);
  };
  try{
    return підставитиШаблон(читати(path.join(джерела, 'показ.html'), 'utf8'), {
      __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка адреси', __ВІДБИТОК__: 'перевірка',
      __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: довідник,
    }).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/,
      '<script>window.loadPyodide=null;</script>');
  }finally{ fs.readFileSync = читати; }
}

(async () => {
  const браузер = await chromium.launch({headless: true});
  try{
    for (const до of [true, false]){
      const стан = до ? 'до' : 'після';
      const html = шаблон(до);
      const контекст = await браузер.newContext({viewport: {width: 390, height: 844}, locale: 'uk-UA'});
      const сторінка = await контекст.newPage();
      const помилки = [];
      сторінка.on('pageerror', п => помилки.push(п.message));
      await сторінка.route('**/*', шлях => шлях.request().isNavigationRequest()
        ? шлях.fulfill({status: 200, contentType: 'text/html; charset=utf-8', body: html}) : шлях.abort());
      await сторінка.goto('https://mightyrochy.github.io/kod-shi-data/показ.html');
      await сторінка.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
      await сторінка.evaluate(() => {
        непідтвердженийМістП = {адреса: 'https://ви.укр/api', токен: ''};
        void підтвердитиАдресуМостаП();
      });
      await сторінка.locator('dialog[open]').waitFor();
      await сторінка.screenshot({path: path.join(__dirname, стан + '-390x844.png')});
      const текст = await сторінка.locator('dialog').innerText();
      fs.writeFileSync(path.join(__dirname, стан + '-екран.txt'), текст + '\nВинятків: ' + помилки.length + '\n', 'utf8');
      if (помилки.length || !текст.includes('Адреса: https://ви.укр/api')) throw new Error(JSON.stringify({стан, помилки, текст}));
      console.log(стан + ': адресу збережено, винятків 0');
      await контекст.close();
    }
  }finally{ await браузер.close(); }
})().catch(п => { console.error(п); process.exitCode = 1; });
