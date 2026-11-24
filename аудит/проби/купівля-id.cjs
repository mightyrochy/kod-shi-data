// Офлайн-регресія: прийнятий find_item -> справжній промпт, без моделі.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');
const джерела = path.resolve(__dirname, '../../джерела');
const source = p => fs.readFileSync(path.join(джерела, p), 'utf8');
const мова = source('показ/мовний_шар.js');
const push = мова.match(/^  const пошук = інструмент .*\n[^\n]*\n  if \(пошук\) вердикти\.push[^\n]*/m)?.[0];
const pack = мова.match(/^  const репліка = Object\.assign\(\{\},\n(?:    [^\n]*\n)*?    частково[^\n]*/m)?.[0];
assert.ok(push && pack, 'межа складання штатної репліки');
const ids = ['ж-тест-1@fixture.invalid','ж-тест-2@fixture.invalid'];
const name = 'Однакова назва';
const statement = (code,values={},item_ids=[]) => ({code,values,item_ids});
const variants = ids.map((ід,n)=>({ід,назва:name,slot:'top',item_type:'sweater',
  вердикт:{повідомлення:{kind:'her_item_verdict',statements:[n ?
    statement('hem_not_judged',{missing:'garment_length'}) :
    statement('hem_on_her_body',{level:'стегно',measured_from:'garment_length'})]}}}));
async function verify(tie, reverse) {
  const choice = tie ? [statement('buy_order_tie',{},ids)] :
    [statement('buy_first',{reasons:['hem_on_her_body'],then:[ids[1]]},[ids[0]])];
  const boundary={варіанти:reverse?[...variants].reverse():variants,
    повідомлення:{kind:'catalogue_search',statements:choice}};
  const ctx=vm.createContext({ЄДИНА_СТОРІНКА:true,вхідМостаП:()=>({}),текстВинятку:e=>e.message,
    містП:async (endpoint,args)=>{
      assert.equal(endpoint,'пошук_речі');assert.equal(args.опис.item_type,'sweater');return boundary;
    }});
  vm.runInContext(source('показ/інструменти.js'),ctx);
  vm.runInContext(`function скласти(інструмент){
    const вердикти=[], пш={}, записаноБезРядка={}, неЗаписано=[], частково=[];
    const додано=null,відповідь='';
    ${push}
    ${pack}
    return репліка;
  }`,ctx);
  const tool=await ctx.інструментомП({name:'find_item',args:{item_type:'sweater'}});
  assert.equal(tool.done,true);
  const p=spawnSync('python3',['-B','-c',[
    'import json, sys, мовний_шар',
    'print(json.loads(мовний_шар.мова(sys.stdin.read()))["промпт"])',
  ].join('\n')],{cwd:джерела,input:JSON.stringify({репліка:ctx.скласти(tool)}),encoding:'utf8'});
  assert.equal(p.status,0,p.stderr);
  const prompt=p.stdout, packed=JSON.parse(prompt.split('\nРЕПЛІКА:\n').at(-1));
  const entries=packed.item_verdicts.slice(0,-1);
  assert.deepEqual(entries.map(v=>v.item_id),boundary.варіанти.map(v=>v.ід),
    'промпт: кожен каталожний вердикт має точний item_id');
  assert.deepEqual(entries.map(v=>v.catalogue_position),[1,2]);
  assert.ok(entries.every(v=>v.item.free_text===name));
  const byId=new Map(entries.map(v=>[v.item_id,v.verdict.statements[0].code]));
  assert.equal(byId.get(ids[0]),'hem_on_her_body');
  assert.equal(byId.get(ids[1]),'hem_not_judged');
  assert.deepEqual(packed.item_verdicts.at(-1).verdict.statements,choice);
  if(tie)assert.doesNotMatch(JSON.stringify(choice),/buy_first/);
  else {
    assert.equal(byId.get(choice[0].item_ids[0]),choice[0].values.reasons[0]);
    assert.equal(byId.get(choice[0].values.then[0]),'hem_not_judged');
  }
  assert.match(prompt,/За нічиєї не називай одного переможця/);
  assert.match(prompt,/Внутрішні ід жінці не показуй/);
}
(async()=>{
  await verify(false,false);
  await verify(false,true);
  await verify(true,true);
  console.log('Купівля, ID: 3/3 (рекомендація, перестановка, нічия)');
})().catch(e=>{console.error(e);process.exitCode=1;});
