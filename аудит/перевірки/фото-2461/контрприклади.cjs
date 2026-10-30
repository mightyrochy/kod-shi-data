const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '../../..');
const source = fs.readFileSync(path.join(root, 'аудит/проби/рв6_стенд.js'), 'utf8');
const start = source.indexOf('речейЗФото.push(await стор.evaluate(');
const end = source.indexOf('\n      }));', start);
assert(start >= 0 && end > start);
const count = eval('(' + source.slice(start + 'речейЗФото.push(await стор.evaluate('.length, end) + '\n})');
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    const photo = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><rect width="40" height="40" fill="blue"/></svg>');
    const fixtures = [
      ['два фото', `<div class="ф"><img src="${photo}"></div><div class="ф"><img src="${photo}"></div>`, '', 2],
      ['дублікат плюс силует', `<div class="ф"><img src="${photo}"></div><div class="ф"><svg></svg></div>`, `<img src="${photo}">`, 1],
      ['силуети', '<div class="ф"><svg></svg></div><div class="ф"><svg></svg></div>', '', 0],
      ['прихована картка', '<div class="ф"><svg></svg></div>', '', 0],
    ];
    for (const [name, collage, extra, expected] of fixtures) {
      await page.setContent(`<div id="картки"><div class="картка" style="display:none"><div class="колаж"><div class="ф"><img src="${photo}"></div></div></div><div class="картка"><div class="колаж">${collage}</div>${extra}</div></div>`);
      await page.waitForFunction(() => [...document.images].every(i => i.complete));
      const value = await page.evaluate(count);
      assert.equal(value, expected, name);
      console.log(name + ': ' + value + ' (очікується ' + expected + ')');
    }
    console.log('Селектор голови PR: 4/4 контрприклади пройдено');
  } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode = 1;});
