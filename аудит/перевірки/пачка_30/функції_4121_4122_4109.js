const { chromium } = require('playwright');
const zlib = require('zlib'), path = require('path');
const карт = {рука:"1",ітерацій:1,викликів:1,текст:"образ",опис:"образ",підпис:"образ",
  речі:[{id:"ж-1@g.com",назва:"Сукня",ціна:3000,слот:"сукня",фото:null},{id:"ж-2@g.com",назва:"Пасок",ціна:500,слот:"пояс",фото:null}],
  мітки:[],знахідки:[],питання:[],етапи:{викликів:1,виклики:[]},свідомі:[],невиконано:null,різноманітність:null,мова:[],мова_спроб:0,мова_видано:"так",фото_не_ті:[],дібрав_код_слоти:[]};
const пакет={в:"ПОКАЗ-V1",збірка:"fn",каталог:"к",профіль:"Оля",розклад:"1234",випадок:"Робота",пул:100,картки:[карт]};
const b64 = zlib.gzipSync(Buffer.from(JSON.stringify(пакет))).toString('base64').replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
(async()=>{
  const br = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const pg = await br.newPage({viewport:{width:390,height:844}});
  const err=[]; pg.on('pageerror',e=>err.push(String(e)));
  await pg.goto('file://'+path.resolve(process.argv[2])+'#'+b64);
  await pg.waitForTimeout(3000); console.log('ERR',err.slice(0,3)); console.log((await pg.evaluate(()=>document.body.innerText)).slice(0,300)); await pg.waitForSelector('#картки .картка .список .річ',{timeout:5000});
  const out = {};
  // 4121
  out.r4121_до = await pg.evaluate(()=>{ відновитиСтанКарткиП(0,{вердикт_людини:'ок',замінити:'ж-1@g.com'},1);
    const к=document.querySelector('#картки .картка'), б=[...к.querySelectorAll('button.замін')];
    return {набір:[...НЕ_ЦЯ_П], напис:б[0].textContent, рядок_замінити:к.querySelector('.річ').classList.contains('замінити'), друга_ні:!к.querySelectorAll('.річ')[1].classList.contains('замінити')};});
  await pg.click('#картки .картка button.замін >> nth=0');
  out.r4121_тап = await pg.evaluate(()=>{const к=document.querySelector('#картки .картка'),б=k=>[...к.querySelectorAll('button.замін')];
    return {набір:[...НЕ_ЦЯ_П], напис:б()[0].textContent, рядок_замінити:к.querySelector('.річ').classList.contains('замінити')};});
  // 4122
  out.r4122 = await pg.evaluate(()=>{const б=document.querySelector('#картки .картка button.замін'), r=б.getBoundingClientRect(), a=getComputedStyle(б,'::after'),
    рядок=б.closest('.річ').getBoundingClientRect();
    const пр=(dx,dy)=>document.elementFromPoint(r.left+r.width/2+dx, r.top+r.height/2+dy)===б;
    return {кнопка_h:Math.round(r.height), after_h:a.height, after_pos:a.position, рядок_h:Math.round(рядок.height),
      тап_вище_20:пр(0,-20), тап_нижче_20:пр(0,20), тап_ліворуч_за_межею:пр(-(r.width/2+4),0), тап_далеко_60:пр(0,-60)};});
  // 4109
  out.r4109 = await pg.evaluate(()=>({
    вигадана: текстомАбоКодамиП({kind:'no_photo_reason',statements:[{code:ЗАЯВА_РІЧ_ВИГАДАНА}]}),
    не_названа: текстомАбоКодамиП({kind:'no_photo_reason',statements:[{code:ЗАЯВА_ПРИЧИНА_НЕ_НАЗВАНА}]}),
    рядок_звіту: [{річ:'Сукня',чому:{kind:'no_photo_reason',statements:[{code:ЗАЯВА_РІЧ_ВИГАДАНА}]}}].map(р=>р.річ+' — '+текстомАбоКодамиП(р.чому)).join(' | ')}));
  await pg.locator('#картки .картка').screenshot({path:process.argv[3]+'/4121_4122_картка.png'});
  console.log(JSON.stringify(out,null,1)); console.log('pageerrors', err.length, err.slice(0,2));
  await br.close();
})();
