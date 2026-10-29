from pathlib import Path
import shutil, json, hashlib, subprocess
root=Path(__file__).resolve().parents[1]
out=root/'аудит/живі_960'
out.mkdir(exist_ok=True)
for name in ['ж1','ж2','ж7']:
    shutil.copy2(Path('C:/tmp/zh0810/R')/(name+'.json'), out/(name+'.json'))
source=root/'аудит/проби/рв6_стенд.js'
s=source.read_text(encoding='utf-8')
start='  async function сцена6(){'
assert s.count(start)==1
s=s.replace(start, start+'''
    await стор.evaluate(()=>{
      window.__960={scene_started:performance.now()};
      new MutationObserver(()=>{
        const e=document.querySelector('#оц-картка .оц-відповідь');
        if(e && e.innerText.trim() && !window.__960.card_ms){
          window.__960.card_ms=performance.now()-window.__960.scene_started;
          window.__960.first_text=e.innerText;
        }
      }).observe(document.body,{subtree:true,childList:true,characterData:true});
    });
''')
needle="    await зібратиТекст('картка «Оціни мій образ»', '#оц-картка');"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
    const вимір960=await стор.evaluate(async()=>{
      const д=document.querySelector('#оц-картка details.оц-не-знаю');
      const result={...window.__960,collapsed_before:д ? !д.open : null};
      if(!д) return {...result,unknowns_missing:true};
      const t=performance.now(); д.open=true;
      await невідомеОцінкиСловамиП(ОЦ.результат.картка,ОЦ.етапи);
      await new Promise(r=>setTimeout(r,150));
      return {...result,expand_ms:performance.now()-t,
        expected_unknowns:ОЦ.результат.картка.не_знаю.length,
        unknown_texts:[...document.querySelectorAll('#оц-картка .оц-не-знаю .задум > div')].map(e=>e.textContent)};
    });
    fs.writeFileSync(path.join(ЗНІМКИ,'timing960.json'),JSON.stringify(вимір960,null,2));
    await знімок('otsinka_unknowns_expanded','#оц-картка');
    await знімок('otsinka_unknowns_expanded_vikno',null,true);
    await зібратиТекст('картка оцінки після розгортання', '#оц-картка');
''')
(root/'аудит/проби/рв6_960_вимір.js').write_text(s,encoding='utf-8')
(out/'instrumentation.diff').write_bytes(subprocess.check_output(['git','diff','--no-index','--',str(source),str(root/'аудит/проби/рв6_960_вимір.js')]) if False else b'')
meta=dict(source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
          runner_original_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
          runner_measured_sha256=hashlib.sha256(s.encode()).hexdigest(),
          site_sha256=hashlib.sha256(Path('C:/tmp/zh960/site/index.html').read_bytes()).hexdigest(),
          independent_acceptance=False, viewport=[390,844], table_comment=6151454756)
(out/'source.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
