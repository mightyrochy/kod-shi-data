const path = require('path'), fs = require('fs'), zlib = require('zlib');
const {chromium} = require('playwright');
const html = path.resolve(process.argv[2]);
const out = path.resolve(process.argv[3]);
fs.mkdirSync(out, {recursive:true});
const packet = {в:'ПОКАЗ-V1', збірка:'b4b52a6d08ef2ed5ffeeb1833b13954e93496318', каталог:'каталог_повний.xml', профіль:'Оля', розклад:'1234', прогін:'пр-2462', випадок:'Літня прогулянка', пул:1,
картки:[{рука:'1', ітерацій:1, викликів:0, текст:'', опис:'', підпис:'образ', речі:[{id:'ж-00001', назва:'Ошатна однотонна жіноча сукня з котоновою підкладкою на літо Dedoce (білий, 36)', ціна:4510, слот:'сукня', фото:'https://bella-bicchi.com/upload/iblock/906/ctirfqztow0p9eju1t0jotwvdp2qr7gv/IMG_3678.jpg'}], мітки:[], знахідки:[], питання:[], етапи:{викликів:0,виклики:[]}, свідомі:[], невиконано:null, різноманітність:null, мова:[], мова_спроб:0, мова_видано:'ні', фото_не_ті:[], дібрав_код_слоти:[]}]};
(async()=>{
 const browser=await chromium.launch({args:['--disable-gpu']});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
  const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
  await page.route(/^https?:/,r=> process.env.FOTO==='1' && r.request().resourceType()==='image' ? r.continue() : r.abort());
  const hash=zlib.gzipSync(Buffer.from(JSON.stringify(packet))).toString('base64url');
  await page.goto(require('url').pathToFileURL(html).href+'#'+hash);
  const card=page.locator('#картки .картка').first(); await card.waitFor({state:'visible',timeout:60000});
  await card.scrollIntoViewIfNeeded();
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('#картки img')).every(x=>x.complete),{},{timeout:30000}).catch(()=>{});
  await page.screenshot({path:path.join(out,'знімок-390x844.png')});
  await card.screenshot({path:path.join(out,'картка-ціла.png')});
  const facts=await card.evaluate(x=>({текст:x.innerText,ширина:x.getBoundingClientRect().width,фото:Array.from(x.querySelectorAll('img')).map(i=>({src:i.src,готове:i.complete,ширина:i.naturalWidth}))}));
  fs.writeFileSync(path.join(out,'знімок.json'),JSON.stringify({FOTO:process.env.FOTO,viewport:'390x844',помилки:errors,картка:facts},null,2));
  console.log(JSON.stringify({помилки:errors,картка:facts},null,2));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
