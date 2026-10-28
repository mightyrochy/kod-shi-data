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
  console.log('Кадри: WebP, хибний MIME, межа розміру, PNG без змін, сирий Claude, FOTO_MAX=0, пошкоджений вхід — гаразд');
})().catch(е => { console.error(е); process.exitCode = 1; });
