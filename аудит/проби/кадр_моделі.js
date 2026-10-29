/* Межа локального рушія: тип визначає вміст кадру, заголовок крамниці — лише підказка. */
const ТИПИ = {jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp', gif: 'image/gif'};
async function підготуватиКадр(байти, тип, {sharp, макс, сире = false}) {
  const прийнятні = сире ? new Set(Object.values(ТИПИ)) : new Set(['image/jpeg', 'image/png']);
  const мета = sharp ? await sharp(байти).metadata() : null;
  const справжній = мета ? (ТИПИ[мета.format] || 'image/' + мета.format) : тип;
  const великий = мета && макс > 0 && Math.max(мета.width || 0, мета.height || 0) > макс;
  const вхід = {заявлений_тип: тип, тип: справжній, байтів: байти.length,
    ширина: мета && мета.width, висота: мета && мета.height};
  тип = справжній;
  if (!прийнятні.has(тип) || великий) {
    if (!sharp) throw Error('тип ' + тип + ' без sharp');
    const кадр = sharp(байти).rotate();
    if (макс > 0) кадр.resize({width: макс, height: макс, fit: 'inside', withoutEnlargement: true});
    байти = await кадр.jpeg({quality: 88}).toBuffer();
    тип = 'image/jpeg';
  }
  return {url: 'data:' + тип + ';base64,' + байти.toString('base64'),
    вхід, вихід: {тип, байтів: байти.length}};
}
module.exports = {підготуватиКадр};
