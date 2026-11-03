/* Знімки чинного показу з річчю каталогу; без викликів моделей. */
const fs = require('node:fs'), path = require('node:path'), zlib = require('node:zlib');
const голова = path.resolve(process.argv[2]), тека = path.resolve(process.argv[3]);
const {chromium} = require(path.join(голова, 'джерела/node_modules/playwright'));
const ш = require(path.join(голова, 'джерела/показ_шаблон.js'));
const дж = path.join(голова, 'джерела');
const html = ш.підставитиШаблон(ш.зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
  __МОДУЛІ_ПОКАЗУ__: 'перевірка приладу', __ЗБІРКА_ПОКАЗУ__: '4552a44d',
  __ВІДБИТОК__: 'перевірка2867', __ФІД_ПОКАЗУ__: 'каталог_повний.xml',
  __КАТАЛОГ_ПОКАЗУ__: 'повний', __ДОВІДНИК_ПОКАЗУ__: ш.прочитатиДовідникJSON(дж)
});
const xml = zlib.gunzipSync(fs.readFileSync(path.join(голова, 'каталог_повний.xml.gz'))).toString('utf8');
const offer = xml.match(/<offer\b[^>]*>[\s\S]*?<\/offer>/)[0];
const поле = п => offer.match(new RegExp('<'+п+'>([\\s\\S]*?)</'+п+'>'))?.[1] || '';
const річ = {id: offer.match(/id="([^"]+)"/)[1], назва: поле('name'), ціна: Number(поле('price')),
  фото: поле('picture'), url: поле('url'), слот: 'сукня'};
const пакет = {в:'ПОКАЗ-V1', збірка:'4552a44d', каталог:'каталог_повний.xml', профіль:'Перевірка',
  розклад:'2867', прогін:'перевірка2867', випадок_рядок:'Перевірка показу речі каталогу', пул:1,
  картки:[{рука:'1', ітерацій:1, викликів:0, текст:'Перевірка показу речі каталогу.',
    опис:'Перевірка показу', підпис:'образ', речі:[річ], мітки:[], знахідки:[], питання:[],
    етапи:{викликів:0,виклики:[]}, свідомі:[], невиконано:null, різноманітність:null,
    мова:[], мова_спроб:0, мова_видано:'так', фото_не_ті:[], дібрав_код_слоти:[]}]};
(async()=>{
  fs.mkdirSync(тека,{recursive:true});
  const браузер = await chromium.launch({headless:true,args:['--disable-gpu']});
  const результати=[];
  try {
    for(const назва of ['до','після']) {
      const ctx=await браузер.newContext({viewport:{width:390,height:844},deviceScaleFactor:1});
      const p=await ctx.newPage(), помилки=[];
      p.on('pageerror',e=>помилки.push(String(e)));
      await p.route('**/*',r=>r.request().url()==='http://review.local/'
        ? r.fulfill({contentType:'text/html',body:html})
        : r.request().resourceType()==='image' ? r.continue() : r.abort());
      await p.goto('http://review.local/');
      await p.waitForFunction(()=>typeof document.getElementById('сцн-новий')?.onclick==='function');
      await p.evaluate(пакет=>{П=пакет;рендер();режим('образи');if(window.показатиОбраз)window.показатиОбраз(0);},пакет);
      await p.waitForSelector('#картки .картка');
      await p.waitForFunction(()=>[...document.querySelectorAll('#картки img')].every(i=>i.complete),null,{timeout:30000}).catch(()=>{});
      await p.screenshot({path:path.join(тека,назва+'-390x844.png'),animations:'disabled'});
      результати.push({назва,помилки,фото:await p.locator('#картки img').evaluateAll(в=>в.map(i=>({src:i.src,ширина:i.naturalWidth}))),
        текст:await p.locator('#картки').innerText()});
      await ctx.close();
    }
    fs.writeFileSync(path.join(тека,'знімок.json'),JSON.stringify({річ,результати},null,2));
    console.log(JSON.stringify({річ,результати},null,2));
  } finally {await браузер.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
