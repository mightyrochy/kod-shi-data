/* ПІКСЕЛІ ВИМІРУ З ФОТО РІЗНОЇ СТОРОНИ (наряд Л-2, 26.09.2026).
   Питання наряду: чи зменшене фото ЩЕ НЕСЕ КОЛІР. Відповідь міряє той самий код,
   що й у продукті: показ вирізає з кадру ≤128×128 RGB (`пікселіРечіП`), а
   `річ_з_фото.виміряти` міряє з них hex і слово. Тут Chromium робить ту саму
   доріжку для кадру телефонної деталізації, зменшеного до кожної сторони, і
   віддає пікселі JSONL — далі їх міряє `джерела/проби/шлях_розмір_фото_колір.py`.
   Запуск: node аудит/проби/фото_колір_сторона.js [файл.jpg ...] > пікселі.jsonl */
const path = require('path');
const {chromium} = require(path.join(__dirname, '..', '..', 'джерела', 'node_modules', 'playwright'));
const fs = require('fs');
const ТЕКА = path.join(__dirname, '..', '..', 'джерела', 'аудит', 'фото_v2');
/* 0 — кадр як є (база порівняння); далі сторони, якими показ шле фото у виклики */
const СТОРОНИ = [0, 1024, 768, 512, 384, 256];
(async () => {
  const бр = await chromium.launch(process.env.PW ? {executablePath: process.env.PW} : {});
  const ст = await бр.newPage();
  await ст.setContent('<html><body></body></html>');
  const файли = process.argv.slice(2).length ? process.argv.slice(2)
    : ['ж-09498@favoriteshoes.com.ua.jpg', 'ж-07773@honchstudio.com.jpg'];
  for (const ф of файли){
    const б64 = fs.readFileSync(path.join(ТЕКА, ф)).toString('base64');
    const р = await ст.evaluate(async ({б64, СТОРОНИ}) => {
      /* КАДР ЯК Є, БЕЗ ЖОДНОГО ПЕРЕМАЛЮВАННЯ. Ні мозаїка (`фото_сторона_симв.js`,
         де міряються символи), ні гладкий розтяг тут не годяться: маска
         `річ_з_фото.маска` шукає ОДНУ пляму речі, і кадр, домальований кодом
         проби, зсунув би саме те, що проба міряє. Тому база — сам знімок, а
         сторони нижче за його бік — справжні зменшення. */
      const телефон = await (await fetch('data:image/jpeg;base64,' + б64)).blob();
      /* ті самі функції, що в показі: спершу JPEG заданої сторони (q 0.7), далі — ≤128 RGB */
      const б64урл = б => btoa(String.fromCharCode(...б)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      const пікселі = async (блоб, сторона) => {
        const бм = await createImageBitmap(блоб);
        const м = сторона ? Math.min(1, сторона / Math.max(бм.width, бм.height)) : 1;
        const w0 = Math.round(бм.width * м), h0 = Math.round(бм.height * м);
        const к1 = document.createElement('canvas'); к1.width = w0; к1.height = h0;
        к1.getContext('2d').drawImage(бм, 0, 0, w0, h0);
        const жпг = await (await fetch(к1.toDataURL('image/jpeg', 0.7))).blob();
        const бм2 = await createImageBitmap(жпг);
        const к2м = Math.min(1, 128 / Math.max(бм2.width, бм2.height));
        const w = Math.max(1, Math.round(бм2.width * к2м)), h = Math.max(1, Math.round(бм2.height * к2м));
        const к2 = document.createElement('canvas'); к2.width = w; к2.height = h;
        const ктх = к2.getContext('2d'); ктх.imageSmoothingEnabled = true; ктх.imageSmoothingQuality = 'high';
        ктх.drawImage(бм2, 0, 0, w, h);
        const rgba = ктх.getImageData(0, 0, w, h).data, rgb = new Uint8Array(w * h * 3);
        for (let i = 0, j = 0; i < rgba.length; i += 4, j += 3){ rgb[j] = rgba[i]; rgb[j+1] = rgba[i+1]; rgb[j+2] = rgba[i+2]; }
        /* симв. жпг тут лише орієнтир: кадр розтягнуто, а не знято телефоном — справжню
           ціну символів міряє `фото_сторона_симв.js` */
        return {сторона, симв_жпг: Math.round(жпг.size * 4 / 3), ширина: w, висота: h, дані: б64урл(rgb)};
      };
      const вих = [];
      for (const с of СТОРОНИ) вих.push(await пікселі(телефон, с));
      return вих;
    }, {б64, СТОРОНИ});
    for (const з of р) console.log(JSON.stringify({річ: ф, ...з}));
  }
  await бр.close();
})();
