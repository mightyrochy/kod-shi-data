const {spawnSync}=require('child_process'),path=require('path');
const root=__dirname;
for(const args of [[path.join(root,'контролі/проба.js')],[path.join(root,'контролі/темна.js')],[path.join(root,'палітра.js'),path.join(root,'after/index.html'),path.join(root,'after'),'strict']]){
 const r=spawnSync(process.execPath,args,{stdio:'inherit',env:process.env});
 if(r.error)throw r.error;
 if(r.status!==0)process.exit(r.status||1);
}
