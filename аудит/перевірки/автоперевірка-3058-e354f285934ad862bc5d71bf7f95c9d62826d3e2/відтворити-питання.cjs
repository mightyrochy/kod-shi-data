const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
// node відтворити-питання.cjs <дерево бази> <дерево голови>
const baseTree = path.resolve(process.argv[2]), headTree = path.resolve(process.argv[3]);
const head = path.join(headTree, 'джерела');
const {JSDOM} = require(require.resolve('jsdom', {paths:[head]}));
const {IDBFactory} = require(require.resolve('fake-indexeddb', {paths:[head]}));
async function probe(tree){
  const src = path.join(tree, 'джерела');
  const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(src,'показ_шаблон'));
  const html = підставитиШаблон(fs.readFileSync(path.join(src,'показ.html'),'utf8')
    .replace('<script src="показ/старт.js"></script>', ''), {
      __МОДУЛІ_ПОКАЗУ__:'', __ЗБІРКА_ПОКАЗУ__:'проба', __ВІДБИТОК__:'abc',
      __ФІД_ПОКАЗУ__:'', __КАТАЛОГ_ПОКАЗУ__:'', __ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(src)
    });
  const dom = new JSDOM(html, {url:'https://example.test/', runScripts:'dangerously', pretendToBeVisual:true,
    beforeParse(w){w.indexedDB=new IDBFactory();w.fetch=async()=>{throw Error('мережі нема')};w.scrollTo=()=>{};w.Element.prototype.scrollIntoView=()=>{};}});
  try{
    const w=dom.window;
    w.eval(`питаннямиП=async()=>{throw Error('text_failed')};чекаютьРозгортанняП=()=>1;
      window._пит=document.createElement('details');
      _пит.innerHTML='<summary>Питання · 2</summary><div class="задум"><div>Чи зручна тобі ця довжина?</div></div>';
      document.body.appendChild(_пит);`);
    const before=w._пит.querySelector('.задум').textContent;
    await w.eval(`дописатиРозгорнутіП({рука:'1',питання_жінці:['Чи зручна тобі ця довжина?']},_пит)`);
    const after=w._пит.querySelector('.задум').textContent;
    return {дерево:tree,до:before,після:after,збережено:after.includes(before),дітей:w._пит.querySelector('.задум').children.length};
  }finally{dom.window.close();}
}
(async()=>{
  const base=await probe(baseTree), headResult=await probe(headTree);
  console.log(JSON.stringify([base,headResult],null,2));
  assert.equal(base.збережено,true);
  assert.equal(headResult.збережено,false);
  console.log('Регресію відтворено: база зберігає питання, голова стирає.');
})().catch(e=>{console.error(e);process.exitCode=1;});
