/* Незалежне декодування всіх збережених кадрів і звірка точного JPEG. */
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
const sharp = require('C:/Users/gemini/kod-shi-test-node/node_modules/sharp');
const crypto = require('crypto');
const root = 'C:/Users/gemini/gemini-runs/w/review-2098-ba986c30';
const p = path.join(root, 'аудит/проби/обгортка-живий/webp');
const {підготуватиКадр} = require(path.join(root,'аудит/проби/кадр_моделі.js'));
(async () => {
  const evidence=[];
  for (const name of fs.readdirSync(path.join(p,'кадри-ДО'))) {
    const input=fs.readFileSync(path.join(p,'кадри-ДО',name));
    const before=await sharp(input).metadata();
    const frame=await підготуватиКадр(input,'image/jpeg',{sharp,макс:1024});
    const bytes=Buffer.from(frame.url.split(',')[1],'base64');
    const after=await sharp(bytes).metadata();
    await sharp(bytes).raw().toBuffer();
    assert(['jpeg','png'].includes(after.format));
    assert(Math.max(after.width,after.height)<=1024);
    const hash=crypto.createHash('sha256').update(bytes).digest('hex');
    if(name==='ж-12335-0.bin') assert.deepEqual(bytes,fs.readFileSync(path.join(p,'кадр-ПІСЛЯ.jpg')));
    evidence.push({файл:name,ДО:[before.format,before.width,before.height,input.length],ПІСЛЯ:[after.format,after.width,after.height,bytes.length],sha256:hash});
  }
  fs.writeFileSync('C:/Users/gemini/gemini-runs/review2098-evidence/кадри-каталогу.json',JSON.stringify(evidence,null,2));
  console.log(JSON.stringify(evidence,null,2));
  console.log('Декодовано без помилок:',evidence.length,'; точний JPEG MustHave збігся');
})().catch(e=>{console.error(e);process.exitCode=1});
