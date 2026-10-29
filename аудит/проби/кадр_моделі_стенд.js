/* Вхід крамниці й готовий base64 мають дати декодований кадр у межі рушія. */
const assert = require('node:assert/strict'), sharp = require('sharp');
const {підготуватиКадр} = require('./кадр_моделі.js');
(async () => {
  const webp = await sharp({create: {width: 1800, height: 1200, channels: 3,
    background: '#9bacbf'}}).webp().toBuffer();
  for (const тип of ['image/webp', 'image/jpeg', 'application/octet-stream']) {
    const к = await підготуватиКадр(webp, тип, {sharp, макс: 1024});
    const б = Buffer.from(к.url.split(',')[1], 'base64');
    const м = await sharp(б).metadata();
    assert.equal(м.format, 'jpeg'); assert.equal(м.width, 1024); assert.equal(м.height, 683);
    assert.equal((await sharp(б).raw().toBuffer()).length, 1024 * 683 * 3);
  }
  const png = await sharp({create: {width: 64, height: 96, channels: 4,
    background: '#abcdef'}}).png().toBuffer();
  const звичайний = await підготуватиКадр(png, 'image/png', {sharp, макс: 1024});
  assert.deepEqual(Buffer.from(звичайний.url.split(',')[1], 'base64'), png);
  const малий = await sharp(webp).resize(64, 32).webp().toBuffer();
  const сирий = await підготуватиКадр(малий, 'image/webp', {sharp, макс: 1024, сире: true});
  assert.deepEqual(Buffer.from(сирий.url.split(',')[1], 'base64'), малий);
  const безМежі = await підготуватиКадр(webp, 'image/jpeg', {sharp, макс: 0});
  assert.equal((await sharp(Buffer.from(безМежі.url.split(',')[1], 'base64')).metadata()).width, 1800);
  await assert.rejects(() => підготуватиКадр(Buffer.from('не зображення'), 'image/jpeg', {sharp, макс: 1024}));
  // Справжній транспорт стенда: обидві форми входу доходять до POST однаково підготовленими.
  const fs = require('fs'), vm = require('vm'), path = require('path');
  const код = fs.readFileSync(path.join(__dirname, 'рв6_стенд.js'), 'utf8');
  const початок = код.indexOf('async function кадрБазою(');
  const кінець = код.indexOf('/* ── ОДИН ВИКЛИК МОДЕЛІ ЧЕРЕЗ', початок);
  const запити = [], втрати = [], журнал = [];
  const живою = vm.runInNewContext(код.slice(початок, кінець) + '\nживоюМоделлю;', {
    fetch: async () => new Response(webp, {status: 200}), Buffer, Date, process,
    _sharp: sharp, підготуватиКадр, ФОТО_МАКС: 1024, ПРИЧИНИ_ВТРАТ: втрати,
    ПРАВИЛА_РЕЧЕННЯМИ: false, КЛОД_ШВОМ: false, ШАР_ВИМКНЕНО: false,
    МОДЕЛЬ_МОВИ_СТЕНДУ: 'мова', МОДЕЛЬ_ЖИВА: 'стилістка', АДРЕСА_МОДЕЛІ: 'http://модель',
    СІД: 3, ТЕМПЕРАТУРА: 0, ТЕМПЕРАТУРА_МОВИ: 0, ВИБІРКА_ЗАПИТУ: () => ({}),
    ЧЕКАЄ_JSON: () => false, ЖУРНАЛ_МОДЕЛІ: журнал,
    постЖСОН: async (url, тіло) => { запити.push(тіло); return {статус: 200, сире: '{}'}; },
  });
  await живою({messages: [{role: 'user', content: [
    {type: 'image', source: {type: 'url', url: 'https://крамниця/кадр.webp'}},
    {type: 'image', source: {type: 'base64', media_type: 'image/jpeg', data: webp.toString('base64')}},
  ]}]}, 'ОПИС_V1', {});
  assert.equal(запити.length, 1); assert.equal(втрати.length, 0);
  assert.equal(журнал[0].кадри.length, 2); assert.equal(журнал[0].фото_не_дійшло, 0);
  for (const б of запити[0].messages[0].content) {
    assert.match(б.image_url.url, /^data:image\/jpeg;base64,/);
    const м = await sharp(Buffer.from(б.image_url.url.split(',')[1], 'base64')).metadata();
    assert.equal(м.format, 'jpeg'); assert.equal(м.width, 1024);
  }
  console.log('Кадри: WebP, хибний MIME, межа розміру, PNG без змін, сирий Claude, FOTO_MAX=0, пошкоджений вхід — гаразд');
})().catch(е => { console.error(е); process.exitCode = 1; });
