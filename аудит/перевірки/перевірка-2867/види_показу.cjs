/* Перевіряє браузерне значення двох синтетичних споживачів, без моделі. */
const fs = require('node:fs'), path = require('node:path');
const {chromium} = require(path.join(path.resolve(process.argv[2]), 'джерела/node_modules/playwright'));
(async()=>{
  const br=await chromium.launch({headless:true,args:['--disable-gpu']});
  try {
    const p=await br.newPage();
    const url='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="red"/></svg>');
    await p.setContent('<picture><source id="preview"><img width="100" height="100"></picture><div id="bg" style="width:100px;height:100px"></div>');
    await p.evaluate(url=>{
      const generate_image=()=>url;
      document.getElementById('preview').srcset=generate_image();
      document.getElementById('bg').style.backgroundImage='url('+generate_image()+')';
    },url);
    await p.waitForFunction(()=>document.querySelector('picture img').naturalWidth===100);
    const r=await p.evaluate(url=>{
      const img=document.querySelector('picture img'), bg=document.getElementById('bg');
      return {picture:{currentSrc_дорівнює_генерації:img.currentSrc===url,naturalWidth:img.naturalWidth,
        видимих_прямокутників:img.getClientRects().length},
        фон:{має_зображення:getComputedStyle(bg).backgroundImage!=='none',
          ширина:bg.getBoundingClientRect().width,висота:bg.getBoundingClientRect().height}};
    },url);
    fs.writeFileSync(process.argv[3],JSON.stringify(r,null,2)+'\n');
    console.log(JSON.stringify(r,null,2));
    if(!r.picture.currentSrc_дорівнює_генерації||!r.фон.має_зображення)process.exitCode=1;
  } finally {await br.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
