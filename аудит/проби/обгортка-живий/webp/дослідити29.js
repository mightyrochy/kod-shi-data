/* Незмінені адреси записаного складу виклику 29; байти повторно отримані з крамниць. */
const fs = require('fs'), path = require('path'), sharp = require('sharp');
const тека = __dirname;
(async () => {
  const речі = JSON.parse(fs.readFileSync(path.join(тека, 'кадри29.json'), 'utf8'));
  const кадри = path.join(тека, 'кадри-ДО'); fs.mkdirSync(кадри, {recursive: true});
  const записи = await Promise.all(речі.flatMap(р => р.фото.slice(0, 3).map(async (url, і) => {
    const запис = {річ: р.id, url};
    try {
      const в = await fetch(url, {signal: AbortSignal.timeout(45000)});
      const б = Buffer.from(await в.arrayBuffer());
      const ім = р.id + '-' + і + '.bin'; fs.writeFileSync(path.join(кадри, ім), б);
      const {format, width, height} = await sharp(б).metadata();
      Object.assign(запис, {http: в.status, mime: в.headers.get('content-type'), байтів: б.length,
        початок: б.subarray(0, 20).toString('hex'), файл: ім, format, width, height});
    } catch (е) { запис.помилка = е.message; }
    return запис;
  })));
  fs.writeFileSync(path.join(тека, 'дослід29.json'), JSON.stringify(записи, null, 2));
  for (const з of записи) console.log(JSON.stringify(з));
})().catch(е => { console.error(е); process.exitCode = 1; });
