const fs=require('fs'),path=require('path'),http=require('http');
const корінь='/home/user/kod-shi-data';
const лінії=JSON.parse(fs.readFileSync(path.join(__dirname,'лінії.json'),'utf8'));
const {зібратиШаблонПоказу,прочитатиДовідникJSON,підставитиШаблон}=require(path.join(корінь,'джерела','показ_шаблон.js'));
const html=підставитиШаблон(зібратиШаблонПоказу(path.join(корінь,'джерела','показ.html')),{
  __МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'проба ДО/ПІСЛЯ',__ВІДБИТОК__:'проба',
  __ФІД_ПОКАЗУ__:'',__КАТАЛОГ_ПОКАЗУ__:'',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(path.join(корінь,'джерела')),
}).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/,'<script>window.loadPyodide=null;</script>');
function пакет(сцена,бік,кнопка){
  return {збірка:'проба',каталог:сцена,профіль:'тест',прогін:сцена+'-'+бік,картки:[{
    рука:'1',текст:'Образ для сцени «'+сцена+'»',опис:'',як_носити:[],речі:[],мітки:[],знахідки:[],
    питання:[],етапи:{},свідомі:[],фото_не_ті:[],дібрав_код_слоти:[],
    питання_жінці:лінії[сцена][бік],питання_кнопка:кнопка}]};
}
(async()=>{
  const сервер=http.createServer((q,в)=>{в.setHeader('Content-Type','text/html; charset=utf-8');в.end(html);});
  await new Promise(r=>сервер.listen(0,'127.0.0.1',r));
  const pw=require(path.join(корінь,'джерела','node_modules','playwright'));
  const браузер=await pw.chromium.launch({headless:true});
  const завд=[
    ['весілля_літо','before','Тут перелік того, що в цьому образі лишилося неперевіреним, бо мені бракує даних про речі, про тебе чи про твій день','до'],
    ['весілля_літо','after','Що я не змогла перевірити','після'],
    ['мороз_ожеледь_офіс','before','Тут перелік того, що в цьому образі лишилося неперевіреним, бо мені бракує даних про речі, про тебе чи про твій день','до'],
    ['мороз_ожеледь_офіс','after','Що я не змогла перевірити','після'],
  ];
  for(const [сцена,бік,кнопка,мітка] of завд){
    const ст=await браузер.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
    await ст.goto('http://127.0.0.1:'+сервер.address().port+'/#модель_мови=нема');
    await ст.waitForFunction(()=>typeof document.getElementById('сцн-новий')?.onclick==='function'||typeof window.рендер==='function',{timeout:15000}).catch(()=>{});
    await ст.evaluate(п=>{window.__п=п;eval('П = window.__п; рендер();');const d=document.querySelector('#картки .питання-коду');if(d)d.open=true;},пакет(сцена,бік,кнопка));
    await ст.waitForTimeout(300);
    const ел=await ст.$('#картки .картка');
    const out=path.join(корінь,'аудит','перевірки','Прогін1-неперевірене-зрозуміло');
    fs.mkdirSync(out,{recursive:true});
    await (ел||ст).screenshot({path:path.join(out,мітка+'-'+сцена+'-390x844.png')});
    console.log('знімок',мітка,сцена,(лінії[сцена][бік]).length,'рядків');
    await ст.close();
  }
  await браузер.close();сервер.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
