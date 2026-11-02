const fs=require('fs'),path=require('path');
const out=path.join(__dirname,'evidence2386');
const {chromium}=require(path.join(__dirname,'pr2386/джерела/node_modules/playwright'));
const photos=JSON.parse(fs.readFileSync(path.join(out,'photos.json'),'utf8')).slice(8);
(async()=>{const b=await chromium.launch({headless:true,args:['--disable-gpu']});const results=[];
try{for(const photo of photos){const p=await b.newPage({viewport:{width:390,height:844},ignoreHTTPSErrors:true});
try{const r=await p.goto(photo.фото,{timeout:30000});const info={ід:photo.ід,адреса:photo.фото,код:r.status(),заголовки:r.headers(),...await p.evaluate(()=>({назва:document.title,картинки:[...document.images].map(i=>({ширина:i.naturalWidth,висота:i.naturalHeight}))}))};
await p.screenshot({path:path.join(out,`direct-${photo.номер}.png`)});results.push(info);
}catch(e){results.push({ід:photo.ід,помилка:String(e)});}finally{await p.close();}}
}finally{await b.close();}fs.writeFileSync(path.join(out,'direct.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
