/* Рядок 5810: дотик по фото міряє річ під пальцем, а не вікно; дотик у тло — виміру нема, причина кодом. Справжній Chromium 390×844 на
   зібраній сторінці, БЕЗ моделі: пікселі дотику `пікселіДотикуП` → міст «перелік» → вимір. Із джерела:  node проби/дотик_маска_5810.js <html> */
const fs = require('fs'), { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true });
    page.setDefaultTimeout(90000);
    await page.route('**/*', r => { const u = new URL(r.request().url());
      if (u.hostname === 'probe.invalid' && u.pathname === '/') return r.fulfill({ contentType: 'text/html', body: fs.readFileSync(process.argv[2], 'utf8') });
      return u.hostname.endsWith('.invalid') ? r.abort() : r.continue(); });
    page.on('pageerror', e => console.log('PAGEERROR', e.message));
    await page.goto('https://probe.invalid/#model_mova=none');
    await page.waitForFunction(() => typeof document.getElementById('оц-оцінити').onclick === 'function');
    const р = await page.evaluate(async () => {
      КОЛІР = { шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', кільце: null, точки: null };
      for (const [і, v] of [['мр-зріст', 167], ['мр-плечі', 96], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 100]]) document.getElementById(і).value = v;
      const к = document.createElement('canvas'); к.width = 600; к.height = 800; const c = к.getContext('2d');
      c.fillStyle = '#8c96a0'; c.fillRect(0, 0, 600, 800); c.fillStyle = '#e6dfd2'; c.fillRect(72, 280, 180, 400); c.fillStyle = '#1d1c1c'; c.fillRect(348, 280, 180, 400);
      const ф = { ід: 'ф2', тип: 'image/jpeg', дані: к.toDataURL('image/jpeg', 0.92).split(',')[1], ширина: 600, висота: 800 };
      const вих = {};
      for (const [назва, х, у] of [['тло', .05, .05], ['тло між речами', .5, .6], ['ботильйон', .27, .6], ['чорний', .73, .6], ['край ботильйона', .125, .36]]){
        const т0 = performance.now(), в = await пікселіДотикуП(ф, х, у);
        const н = await містП('оцінка', Object.assign(вхідОцінкиП(), { крок: 'перелік', речі: [{ ід: 'н1', слот: 'взуття', дотик: true, фото: 'ф2', рамка: в.рамка }], пікселі: { н1: в.пікселі } }));
        вих[назва] = { hex: (н.hex || {}).н1 || null, мс: Math.round(performance.now() - т0) };
      }
      return вих; });
    for (const [н, в] of Object.entries(р)) console.log(н.padEnd(16), String(в.hex).padEnd(8), в.мс + ' мс');
  } finally { await browser.close(); }
})();
