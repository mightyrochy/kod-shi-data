const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../джерела/показ');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const f=(src,name)=>src.match(new RegExp('^function '+name+'\\([\\s\\S]*?^}','m'))?.[0];
const screen=read('екран/картка.js');
const ids=['ж-тест-1@fixture.invalid','ж-тест-2@fixture.invalid'];
const variants=ids.map((ід,i)=>({ід,назва:'Дві однакові назви',url:'https://fixture.invalid/item/'+(i+1),
  фото:i?['https://fixture.invalid/не-вантажиться']:[],slot:'top',item_type:'sweater',
  вердикт:{повідомлення:{kind:'her_item_verdict',statements:[{code:i?'hem_on_her_body':'hem_not_judged'}]}}}));
const noop=()=>{};
function env(){
  function el(tag,className='',textContent=''){
    return {tag,className,textContent,children:[],style:{},
      appendChild(child){this.children.push(child);child.parent=this;return child;},
      replaceWith(child){assert.ok(this.parent,'кадр має бути вставлений до синхронної заміни');const parent=this.parent;
        parent.children.splice(parent.children.indexOf(this),1,child);child.parent=parent;this.parent=null;}};
  }
  const ctx=vm.createContext({ел:el,елЖінціП:el,document:{createElement:el},своїЕкрануП:noop,розміткаЖінціП:noop,
    текстЖінціП:(e,t)=>e.textContent=t,крамниця:()=>'',грн:()=>'',підписБезНазвиП:()=>'',clearTimeout,setTimeout,
    ЄДИНА_СТОРІНКА:true,вхідМостаП:()=>({}),текстВинятку:e=>e.message,
    містП:async n=>{assert.equal(n,'пошук_речі');return {варіанти:variants};}});
  for (const [src,name] of [[read('картки.js'),'кадриРечі'],[screen,'підставитиКадр'],[screen,'рядокЗмінноїПари']]){
    const body=f(src,name);assert.ok(body,name);vm.runInContext(body,ctx);
  }
  vm.runInContext(screen.match(/^function силуетКадру.*$/m)[0],ctx);
  vm.runInContext(read('екран/інструмент.js'),ctx);
  vm.runInContext(read('інструменти.js'),ctx);
  return ctx;
}
function all(n){return [n,...n.children.flatMap(all)];}
const img=n=>all(n).find(x=>x.tag==='img');
function exhaust(n){const i=img(n);assert.ok(i?.src);i.onerror();i.onerror();}
async function tool(c){return c.інструментомП({name:'find_item',args:{item_type:'sweater'}});}
function stillVisible(row,n,href){
  assert.notEqual(row.style.display,'none','рядок покупки не ховається через фото');
  assert.ok(all(row).some(x=>x.className==='арка'),'збережений штатний силует');
  assert.ok(all(row).some(x=>x.textContent==='Варіант '+n),'видима точна позиція');
  assert.ok(all(row).some(x=>x.tag==='a'&&x.href===href&&x.textContent==='Дві однакові назви'),'назва та посилання');
  assert.ok(all(row).every(x=>!String(x.textContent).includes('@fixture.invalid')),'внутрішній ID не малюється');
}
test('купівля: нуль кадрів не зсуває видиму позицію',async()=>{
  const c=env(),out=await tool(c),ui=c.карткаІнструментаП(out);
  assert.equal(ui.children.length,2);
  stillVisible(ui.children[0],1,variants[0].url);
  assert.equal(out.catalogue_search.variants[0].item_id,ids[0]);
  assert.equal(out.catalogue_search.variants[0].catalogue_position,1);
  assert.equal(out.catalogue_search.variants[0].verdict.statements[0].code,'hem_not_judged');
});
test('купівля: виснажений кадр не прибирає другий однойменний варіант',async()=>{
  const c=env(),out=await tool(c),ui=c.карткаІнструментаП(out);
  exhaust(ui.children[1]);
  stillVisible(ui.children[1],2,variants[1].url);
  assert.equal(out.catalogue_search.variants[1].item_id,ids[1]);
  assert.equal(out.catalogue_search.variants[1].catalogue_position,2);
  assert.equal(out.catalogue_search.variants[1].verdict.statements[0].code,'hem_on_her_body');
});
test('решта викликів рядка не отримує позиції й ховається без кадру як раніше',()=>{
  const c=env(),a=c.рядокЗмінноїПари({фото:''}),b=c.рядокЗмінноїПари({фото:'fixture:bad'});
  exhaust(b);
  for(const n of [a,b]){
    assert.equal(n.style.display,'none');assert.ok(all(n).every(x=>!String(x.textContent).includes('Варіант')));
  }
});
