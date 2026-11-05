const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
// node відтворити-питання-браузер.cjs <дерево бази> <дерево голови> <тека знімків>
const baseTree=path.resolve(process.argv[2]),headTree=path.resolve(process.argv[3]);
const head=path.join(headTree,'джерела');
const {chromium}=require(require.resolve('playwright',{paths:[head]}));
const out=path.resolve(process.argv[4]);
(async()=>{
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({headless:true});
  try{
    for(const [label,tree] of [['база-3058',baseTree],['голова-3058',headTree]]){
      const src=path.join(tree,'джерела');
      const {підставитиШаблон,прочитатиДовідникJSON}=require(path.join(src,'показ_шаблон'));
      const html=підставитиШаблон(fs.readFileSync(path.join(src,'показ.html'),'utf8'),{
        __МОДУЛІ_ПОКАЗУ__:'',__ЗБІРКА_ПОКАЗУ__:'проба',__ВІДБИТОК__:'abc',
        __ФІД_ПОКАЗУ__:'',__КАТАЛОГ_ПОКАЗУ__:'',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(src)});
      const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
      await page.route('**/*',route=>route.request().url()==='https://example.test/'
        ?route.fulfill({contentType:'text/html; charset=utf-8',body:html}):route.abort());
      await page.goto('https://example.test/');
      await page.waitForFunction(()=>!!document.getElementById('сц-новий').onclick);
      const result=await page.evaluate(async()=>{
        питатиПачкамиП=async()=>{throw Error('text_failed')};
        const к={рука:'1',питання_жінці:['Чи зручна тобі ця довжина?'],питання:[
          {текст:'Чи зручна тобі ця довжина?',повідомлення:{kind:'question_existing'}},
          {на_розгортання:true,повідомлення:{kind:'question_deferred'}}]};
        const панель=document.createElement('section');
        панель.style.cssText='position:fixed;inset:100px 16px auto;background:var(--полотно);padding:20px;z-index:2000;border:1px solid currentColor';
        панель.innerHTML='<h2>Питання до образу</h2><details open><summary>Питання · 2</summary><div class="задум"><div>Чи зручна тобі ця довжина?</div></div></details>';
        document.body.appendChild(панель);
        const пит=панель.querySelector('details'),до=пит.querySelector('.задум').textContent;
        const чекають=чекаютьРозгортанняП(к);
        await дописатиРозгорнутіП(к,пит);
        const після=пит.querySelector('.задум').textContent;
        return {до,після,чекають,збережено:після.includes(до)};
      });
      console.log(label,JSON.stringify(result));
      assert.equal(result.чекають,1);
      assert.equal(result.збережено,label==='база-3058');
      await page.screenshot({path:path.join(out,label+'.png'),animations:'disabled'});
      await page.close();
    }
    console.log('Chromium 390×844: регресію підтверджено через справжні чекаютьРозгортанняП і питаннямиП.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
