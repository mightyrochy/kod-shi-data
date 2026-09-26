/* СКІЛЬКИ СИМВОЛІВ BASE64 КОШТУЄ ФОТО РЕЧІ НА КОЖНІЙ СТОРОНІ (наряд Л-2, 26.09.2026).
   Міряє СПРАВЖНІЙ Chromium тим самим полотном, що й показ (createImageBitmap →
   canvas → JPEG), бо арифметикою цього не взяти: розмір JPEG залежить від
   деталізації кадру, а не лише від пікселів. Числа звідси стоять причиною біля
   `СТОРОНА_ФОТО_*_П` у `показ.html`.
   Запуск: node аудит/проби/фото_сторона_симв.js <файл.jpg> [...]
     (типово — дві речі з фіду; PW=<шлях до chrome> задає інший бінарник) */
const {chromium} = require(require('path').join(__dirname, '..', '..', 'джерела', 'node_modules', 'playwright'));
const fs = require('fs'), path = require('path');
/* БІНАРНИК БРАУЗЕРА: `PW`/`CHROMIUM`, а інакше — той, що вже лежить у образі
   (`PLAYWRIGHT_BROWSERS_PATH`). Без цього проба падала там, де Chromium є, але
   версія його теки не та, якої чекає свіжий playwright. */
function хром(){
  for (const ш of [process.env.PW, process.env.CHROMIUM]) if (ш && fs.existsSync(ш)) return ш;
  const база = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
  try{
    for (const т of fs.readdirSync(база).filter(x => /^chromium-\d+$/.test(x)).sort().reverse()){
      const ш = path.join(база, т, 'chrome-linux', 'chrome');
      if (fs.existsSync(ш)) return ш;
    }
  }catch(_){ }
  return null;
}
const ТЕКА = path.join(__dirname, '..', '..', 'джерела', 'аудит', 'фото_v2');
(async () => {
  const бр = await chromium.launch(хром() ? {executablePath: хром()} : {});
  const ст = await бр.newPage();
  await ст.setContent('<html><body></body></html>');
  const файли = process.argv.slice(2).length ? process.argv.slice(2)
    : ['ж-09498@favoriteshoes.com.ua.jpg', 'ж-07773@honchstudio.com.jpg'];
  for (const ф of файли){
    const б64 = fs.readFileSync(path.join(ТЕКА, ф)).toString('base64');
    const р = await ст.evaluate(async ({б64}) => {
      const бл = await (await fetch('data:image/jpeg;base64,' + б64)).blob();
      const бм0 = await createImageBitmap(бл);
      /* ФОТО ТЕЛЕФОНОМ: каталожний кадр 500–700 px — це вже зменшений знімок
         крамниці. Щоб міряти те, що справді приходить із телефона, кадр
         збирається сіткою 4×4 з СЕБЕ САМОГО зі зсувом — деталізація лишається
         фотографічною, а розмір стає телефонним (≈2800 px). */
      const N = 4, W = бм0.width * N, H = бм0.height * N;
      const к0 = document.createElement('canvas'); к0.width = W; к0.height = H;
      const к = к0.getContext('2d');
      for (let y = 0; y < N; y++) for (let x = 0; x < N; x++)
        к.drawImage(бм0, x * бм0.width, y * бм0.height);
      const вих = {джерело: [бм0.width, бм0.height], телефон: [W, H]};
      const телефонБлоб = await new Promise(r => к0.toBlob(r, 'image/jpeg', 0.92));
      вих.телефон_симв = Math.round(телефонБлоб.size * 4 / 3);
      const бм = await createImageBitmap(телефонБлоб);
      вих.по_стороні = {};
      for (const с of [1568, 1024, 768, 512, 384, 256]){
        const м = Math.min(1, с / Math.max(бм.width, бм.height));
        const w = Math.round(бм.width * м), h = Math.round(бм.height * м);
        const кан = document.createElement('canvas'); кан.width = w; кан.height = h;
        кан.getContext('2d').drawImage(бм, 0, 0, w, h);
        вих.по_стороні[с] = {};
        for (const я of [0.85, 0.7, 0.55])
          вих.по_стороні[с][я] = кан.toDataURL('image/jpeg', я).split(',')[1].length;
      }
      return вих;
    }, {б64});
    console.log(ф, JSON.stringify(р));
  }
  await бр.close();
})();
