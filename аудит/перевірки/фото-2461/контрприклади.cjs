const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
const корінь = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '../../..');
const текст = fs.readFileSync(path.join(корінь, 'аудит/проби/рв6_стенд.js'), 'utf8');
const початок = текст.indexOf('речейЗФото.push(await стор.evaluate(');
const кінець = текст.indexOf('\n      }));', початок);
assert(початок >= 0 && кінець > початок);
const лічити = eval('(' + текст.slice(початок + 'речейЗФото.push(await стор.evaluate('.length, кінець) + '\n})');
(async () => {
  const браузер = await chromium.launch();
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}});
    const фото = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="blue"/></svg>');
    const приклади = [
      ['два фото', `<div class="ф"><img src="${фото}"></div><div class="ф"><img src="${фото}"></div>`, '', 2],
      ['дублікат плюс силует', `<div class="ф"><img src="${фото}"></div><div class="ф"><svg></svg></div>`, `<img src="${фото}">`, 1],
      ['силуети', '<div class="ф"><svg></svg></div><div class="ф"><svg></svg></div>', '', 0],
      ['прихована картка', '<div class="ф"><svg></svg></div>', '', 0],
    ];
    for (const [назва, колаж, додаткове, очікується] of приклади) {
      await стор.setContent(`<div id="картки"><div class="картка" style="display:none"><div class="колаж"><div class="ф"><img src="${фото}"></div></div></div><div class="картка"><div class="колаж">${колаж}</div>${додаткове}</div></div>`);
      await стор.waitForFunction(() => [...document.images].every(і => і.complete));
      const число = await стор.evaluate(лічити);
      assert.equal(число, очікується, назва);
      console.log(назва + ': ' + число + ' (очікується ' + очікується + ')');
    }
    console.log('Селектор голови PR: 4/4 контрприклади пройдено');
  } finally {await браузер.close();}
})().catch(помилка => {console.error(помилка); process.exitCode = 1;});
