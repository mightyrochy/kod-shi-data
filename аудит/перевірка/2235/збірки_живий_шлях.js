const {spawnSync}=require('child_process');const {живийШлях}=require(process.cwd()+'/аудит/проби/нова_база.js');
const g=(...a)=>spawnSync('git',['-c','core.quotepath=false',...a],{cwd:process.cwd(),encoding:'utf8'});
const шлях=живийШлях(process.cwd());
let з=0,без=0,інші=0;
for(const B of g('log','--since=2026-10-26','--format=%H','--author=github-actions','origin/main','--','build.txt').stdout.trim().split('\n')){
 const S=g('show',B+':build.txt').stdout.trim(); if(g('cat-file','-e',S).status) continue;
 const a=g('diff','--name-only',S,B,'--',...шлях).stdout.trim().split('\n').filter(Boolean);
 const b=g('diff','--name-only',S,B,'--',...шлях,':(exclude)джерела/аудит/ДОСЯЖНІСТЬ.md').stdout.trim();
 if(a.length)з++; if(!b)без++; else інші++;
}
console.log('збірок з відмінністю у живому шляху (ДОСЯЖНІСТЬ чи інше):',з,'; з відмінністю лише НЕ в ДОСЯЖНІСТЬ.md:',інші,'; чисто без ДОСЯЖНІСТЬ.md:',без);
