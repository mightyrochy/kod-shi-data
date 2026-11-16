const fs = require('fs'), path = require('path'), cp = require('child_process'), Module = require('module');
const корінь = process.cwd(), джерела = path.join(корінь, 'джерела'), тека = path.join(корінь, 'аудит/перевірки/gemini-Е2-текст-жінці-доробка-8');
const файл = path.join(джерела, 'тест_показу.js');
const звіт = JSON.parse(fs.readFileSync('аудит/проби/Е1-нічний-живий-20261107/ж5_співбесіда_без/вердикти.txt', 'utf8'));
const річ = звіт.прогони.flatMap(прогін => прогін.вердикти).find(вердикт => String(вердикт.рука) === '1').речі_образу.find(р => р.фото && р.урл);
const {chromium} = require(path.join(джерела, 'node_modules/playwright'));
(async () => {
 const браузер = await chromium.launch({headless:true});
 const результат = {};
 try {
  for (const етап of ['до','після']) {
   global.__шаблонДоробки = розмітка => етап === 'після' ? розмітка : розмітка.replace(fs.readFileSync(path.join(джерела, 'показ/мовний_шар.js'),'utf8'), () => cp.execFileSync('git',['show','9fbe43f86920fa6d3da73eb145ee4db4cbc091f1:джерела/показ/мовний_шар.js'],{encoding:'utf8',maxBuffer:1000000}));
   let префікс = fs.readFileSync(файл,'utf8').split('(async () => {')[0]
    .replace('const ЗІБРАНИЙ = process.argv[2] ? path.resolve(process.argv[2]) : null;', 'const ЗІБРАНИЙ = null;')
    .replace('const шаблон = зібратиШаблонПоказу(ЗІБРАНИЙ || path.join(__dirname, "показ.html"));','const шаблон = global.__шаблонДоробки(зібратиШаблонПоказу(ЗІБРАНИЙ || path.join(__dirname, "показ.html")));');
   const модуль = new Module(файл); модуль.filename=файл; модуль.paths=Module._nodeModulePaths(джерела);
   модуль._compile(префікс+'\nmodule.exports={сторінка,чекатиСтарт};',файл);
   const {w,помилки} = модуль.exports.сторінка({url:'https://example.test/#модель_мови=нема'});
   await модуль.exports.чекатиСтарт(w); w.__річДоробки=річ;
   const тексти = w.eval(`(() => {
    П={картки:[{рука:'1',текст:'Образ',опис:'Ці речі поєднуються.',як_носити:[],замінено:'Please retry later',
      речі:[window.__річДоробки],мітки:[],знахідки:[],питання:[],етапи:{},свідомі:[],фото_не_ті:[],дібрав_код_слоти:[]}]};
    const картка=рендерКартку(0); картка.querySelector('.річ .н').appendChild(елЖінціП('div','заміни-нема','', 'replacement_not_found'));
    document.body.appendChild(картка); for (const вузол of document.body.children) if (вузол !== картка) вузол.hidden = true;
    return {відмова:картка.querySelector('.заміни-нема').textContent,пояснення:ШАБЛОНИ_ЗБОЮ_П.card_replacement_failed,
      сторож:['replacement_not_found','card_replacement_failed'].map(k=>станТекстуЖінціП(ШАБЛОНИ_ЗБОЮ_П[k]))};
   })()`);
   const розмітка=w.document.documentElement.outerHTML.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,''); w.close();
   const сторінка=await браузер.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
   await сторінка.route('**/*',р=>р.request().resourceType()==='image'?р.continue():р.abort());
   await сторінка.setContent(розмітка,{waitUntil:'networkidle'});
   const вигляд=await сторінка.evaluate(()=>({переповнення:document.documentElement.scrollWidth>innerWidth,фото:[...document.images].map(i=>({адреса:i.src,ширина:i.naturalWidth}))}));
   await сторінка.screenshot({path:path.join(тека,етап+'-390x844.png'),fullPage:true}); await сторінка.close();
   результат[етап]={...тексти,...вигляд,помилки};
  }
 } finally {await браузер.close();}
 fs.writeFileSync(path.join(тека,'екран.json'),JSON.stringify(результат,null,2));
 console.log(JSON.stringify(результат));
})().catch(e=>{console.error(e);process.exitCode=1});