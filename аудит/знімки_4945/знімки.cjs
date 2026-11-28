const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');

const [режим, тека, кеш, докази = __dirname] = process.argv.slice(2);
const стани = [
  ['хвоя', 'д7·холодна·14·середні', 'темна хвоя'],
  ['чорнослив', 'д2·холодна·14·середні', 'чорнослив'],
  ['капучино', 'д3·тепла·68·середні', 'капучино'],
];
const схеми = [
  'нейтрали+акцент', 'тональна', 'аналогова', 'приглушена_комплементарна', 'тріада', 'контраст-мисматч'
];
const базова = JSON.parse(fs.readFileSync(path.join(тека, 'джерела/стенд_вх.json'), 'utf8'));
const жінка = ім => JSON.parse(fs.readFileSync(path.join(тека, 'аудит/проби/жінки', ім + '.json'), 'utf8'));
const профілі = {
  стенд: {skin:[базова.шкіра], hair:базова.волосся, eyes:базова.очі},
  ж1: жінка('ж1'),
  ж3: жінка('ж3'),
};
function чип(стор, дія, ключ = '') {
  return стор.locator('[data-ключ="' + дія + ':' + ключ + '"]');
}
async function тап(стор, ціль) {
  await стор.evaluate(() => window.минуліБарви = ПАЛІТРА);
  await ціль.click();
  await стор.waitForFunction(() => !!ПАЛІТРА && ПАЛІТРА !== window.минуліБарви);
}
async function main() {
  const браузер = await chromium.launch({executablePath: '/usr/bin/chromium', headless:true, args:['--no-sandbox']});
  const довідка = [];
  try {
    const джерело = 'http://127.0.0.1:8765';
    for (const [профіль, ж] of Object.entries(профілі)) {
      const стор = await браузер.newPage({viewport:{width:390,height:844}, deviceScaleFactor:1, isMobile:true, hasTouch:true});
      стор.setDefaultTimeout(45000);
      стор.on('pageerror', e => console.error('Помилка сторінки:', e.message));
      await стор.route('**/*', async route => {
        const u = new URL(route.request().url());
        if (u.origin === джерело && u.pathname === '/') return route.fulfill({
          status:200, contentType:'text/html; charset=utf-8', path:path.join(докази, режим, 'index.html'),
        });
        if (u.origin === 'https://cdn.jsdelivr.net' && u.pathname.startsWith('/pyodide/')) {
          const ім = path.basename(u.pathname);
          const тип = ім.endsWith('.wasm') ? 'application/wasm' : ім.endsWith('.js')
            ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
          const файл = path.join(кеш, ім);
          if (!fs.existsSync(файл)) return route.fulfill({status:404,body:ім});
          return route.fulfill({status:200,contentType:тип,path:файл});
        }
        return route.abort();
      });
      await стор.goto(джерело, {waitUntil:'domcontentloaded'});
      await стор.waitForFunction(() => Екран.стан.запущено === true);
      await стор.evaluate(ж => {
        КОЛІР = {...КОЛІР, шкіра:ж.skin[0], волосся:ж.hair[0], очі:ж.eyes,
          кільце:ж.ring || null, точки:{шкіра:ж.skin,волосся:ж.hair}};
        режим('палітра');
      }, ж);
      await стор.waitForFunction(() => ПАЛІТРА?.гілки?.length === 6, null, {timeout:90000});
      await тап(стор, чип(стор, 'палітра-гама', 'середні'));
      await тап(стор, чип(стор, 'палітра-схема', 'тріада'));
      let попередні = await стор.evaluate(() => Object.fromEntries(ПАЛІТРА.гілки.map(г=>[г.схема, г.зразки])));
      for (const [назва, ключ, очікуванаНазва] of стани) {
        const ціль = чип(стор, 'палітра-основа', ключ);
        await стор.evaluate(() => { const д = document.querySelector('#пал-основа details'); if (д) д.open = true; });
        if (!(await ціль.textContent()).toLowerCase().includes(очікуванаНазва)) {
          throw new Error('Назва: ' + await ціль.textContent());
        }
        await тап(стор, ціль);
        await стор.evaluate(() => {
          const д = document.querySelector('#пал-основа details');
          if (д) д.open = false;
          document.querySelector('#пал-схема').scrollIntoView({block:'center'});
        });
        await стор.waitForFunction(() => {
          const кольори = селектор => [...document.querySelectorAll(селектор)]
            .map(і => і.style.backgroundColor).join('/');
          const видимі = кольори('#mirror-my-colors .стрічка i');
          return видимі && видимі === кольори('#пал-стрічка i');
        });
        const стан = await стор.evaluate(() => {
          const основа = ВИБІР.вибір_кольору.база_hex;
          const rgb = hex => 'rgb(' + hex.slice(1).match(/../g).map(к => parseInt(к, 16)).join(', ') + ')';
          return {
            основа, основаRgb:rgb(основа),
            смуга: [...document.querySelectorAll('#mirror-my-colors .стрічка i')].map(і=>і.style.backgroundColor),
            плитки: ПАЛІТРА.гілки.map(г => {
              const ч = [...document.querySelectorAll('#пал-схема .чип')]
                .find(е=>е.dataset.ключ === 'палітра-схема:' + г.схема);
              const орієнтир = ч.querySelector('.орієнтир-тону');
              return {назва:г.схема, зразки:г.зразки, підпис:ч.textContent,
                основаПозаВікнами:г.основа_поза_вікнами,
                першийКолір:ч.querySelector('i')?.style.backgroundColor || null,
                орієнтир:орієнтир?.textContent || null,
                зразкиRgb:г.зразки.map(rgb),
                кольори:[...ч.querySelectorAll('.зразки i')].map(і=>і.style.backgroundColor)};
            })
          };
        });
        const тріада = стан.плитки.find(п => п.назва === 'тріада');
        if (режим === 'після') {
          for (const плитка of стан.плитки.filter(п => п.зразки.length)) {
            if (плитка.першийКолір !== стан.основаRgb ||
                JSON.stringify(плитка.кольори) !== JSON.stringify(плитка.зразкиRgb) ||
                (плитка.основаПозаВікнами ?
                  !плитка.орієнтир?.includes('поза добором') || плитка.зразки.includes(стан.основа) :
                  плитка.орієнтир || плитка.зразки[0] !== стан.основа)) {
              throw new Error('Плитка не показує основу й допустимі зразки: ' + JSON.stringify(плитка));
            }
          }
        }
        if (режим === 'після' && JSON.stringify(стан.смуга) !== JSON.stringify(тріада.кольори)) {
          throw new Error('Смужка відрізняється від плитки: ' + JSON.stringify(стан));
        }
        const поточні = Object.fromEntries(стан.плитки.map(п=>[п.назва, п.зразки]));
        const зміни = схеми.filter(с => JSON.stringify(попередні[с]) !== JSON.stringify(поточні[с]));
        попередні = поточні;
        довідка.push({профіль, назва, зміни, ...стан});
        await стор.screenshot({path:path.join(докази, режим, профіль + '-' + назва + '.png')});
        if (профіль === 'стенд' && назва === 'хвоя') {
          await стор.locator('#mirror-my-colors .стрічка').scrollIntoViewIfNeeded();
          await стор.screenshot({path:path.join(докази, режим, 'стенд-хвоя-стрічка.png')});
        }
        console.log(режим, профіль, очікуванаНазва, стан.основа, зміни.length + '/6', '#пал-стрічка', стан.смуга.join(' '));
      }
      await стор.close();
    }
  } finally { await браузер.close(); }
  fs.writeFileSync(path.join(докази, режим, 'плитки.json'), JSON.stringify(довідка,null,2));
}
main().catch(e => { console.error(e); process.exitCode = 1; });
