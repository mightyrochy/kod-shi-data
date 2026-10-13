/* Блідий останній рядок переліку на картці — це сходинка появи, а не сталий стан.
   Бере ПРАВИЛА З `показ.html` (нічого не вигадує), малює шість рядків `.річ` у
   справжньому Chromium і друкує непрозорість ОСТАННЬОГО рядка в часі.
   Запуск: CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=<playwright> node цей_файл */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ПОКАЗ = fs.readFileSync(path.join(__dirname, '..', '..', 'джерела', 'показ.html'), 'utf8');
const правила = ПОКАЗ.split('\n').filter(р =>
  /^\.річ\{|^\s+animation:нанизати|^\.річ:nth-child|^@keyframes нанизати/.test(р)).join('\n');
const сторінка = '<!doctype html><meta charset="utf-8"><style>\n' + правила
  + '\n</style><div class="список">' + '<div class="річ">річ</div>'.repeat(6) + '</div>';

(async () => {
  console.log('правила, взяті з показ.html:');
  console.log(правила.split('\n').map(р => '   ' + р.trim().slice(0, 110)).join('\n'));
  const бр = await chromium.launch({ executablePath: process.env.CHROMIUM });
  const стор = await (await бр.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  const t0 = Date.now();
  await стор.setContent(сторінка);
  const заміри = [];
  for (const мс of [0, 100, 200, 300, 500, 700, 1000, 2000]) {
    while (Date.now() - t0 < мс) await new Promise(р => setTimeout(р, 5));
    заміри.push([мс, await стор.evaluate(() => [...document.querySelectorAll('.річ')]
      .map(е => Number(getComputedStyle(е).opacity).toFixed(2)))]);
  }
  for (const [мс, ряд] of заміри)
    console.log('   +' + String(мс).padStart(4) + ' мс від появи · непрозорість рядків 1…6:', ряд.join(' '));
  const остан = заміри[заміри.length - 1][1];
  console.log('останній рядок стає повністю видимим; блідим він БУВАЄ доти, доки триває сходинка',
    '(затримка ' + (ПОКАЗ.match(/animation-delay:calc\(var\(--і,0\) \* (\d+)ms\)/) || [, '?'])[1] + ' мс × номер рядка'
    + ' + тривалість ' + (ПОКАЗ.match(/animation:нанизати ([\d.]+)s ease-out both/) || [, '?'])[1] + ' с)');
  console.log('   стан у кінці:', остан.join(' '), '· однакові:', new Set(остан).size === 1);
  await бр.close();
})();
