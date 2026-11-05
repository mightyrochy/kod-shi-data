"""Відтворення 12969 на заданому дереві PR, без викликів моделей і правок коду."""
import json
import pathlib
import subprocess
import sys

корінь = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(корінь / "джерела"))
import пакет_моделі as П
import уважний_вибір as У
import знання_дріт as З

речі = []
for і, тип in enumerate(("blouse", "blouse", "tshirt")):
    колір = {"lab": (20 + і, 1, 2)} if і < 2 else {
        "hex": "#123456", "колір_не_вимір": {"вікно": [10, 30, 0, 5, None]}}
    річ = П.річ_пулу(dict(id=str(і), тип=тип, **колір), {})
    річ["н"] = "#1·%02d" % (і + 1)
    речі.append(річ)
запит = У.запити_оцінки({"пул": {"верх": речі}}, {р["н"] for р in речі}, 1, 0)[0]
дані = json.loads(запит["текст"])
З.відновити(дані)
print("ДО: штатний запит оцінки, легенда відновлюється", flush=True)

код = r"""
const fs=require('fs'), vm=require('vm'), path=require('path');
const root=process.argv[1];
const cards=fs.readFileSync(path.join(root,'джерела/показ/картки.js'),'utf8');
const bridge=fs.readFileSync(path.join(root,'джерела/показ/міст.js'),'utf8');
const fn=cards.slice(cards.indexOf('const РЕЄСТР_ЗАМІНИ_П'),cards.indexOf('async function замінитиРічП'));
if (!fn.includes('function вміститиКандидатівЗаміниП')) throw Error('На цьому дереві немає правила PR');
const math=bridge.slice(bridge.indexOf('function оцінкаТокенівП'),bridge.indexOf('/* Оцінює токени кадру'));
const ctx=vm.createContext({prompt:JSON.parse(fs.readFileSync(0,'utf8'))});
vm.runInContext(`const МОДЕЛЬ_П='qa', МАКС_ТОКЕНІВ_П=4000;
const НАЛАШТУВАННЯ_РУШІЯ_П={qa:{}};
const ПОПРАВКИ_ТОКЕНІВ_П={}, ПОПРАВКА_ТОКЕНІВ_ПОЧАТКОВА_П=1.1;
const стадіяВикликуП=()=>'';`+math+fn+`
const before=JSON.stringify(prompt), copy=JSON.parse(before);
Object.values(copy.items)[0].splice(1,1);
const estimate=t=>_оцінкаПромптаП([{role:'user',content:[{type:'text',text:t}]}],'qa|');
НАЛАШТУВАННЯ_РУШІЯ_П.qa.loaded_context_length=estimate(JSON.stringify(copy))+МАКС_ТОКЕНІВ_П;
const req={текст:before,скорочено:[]}; вміститиКандидатівЗаміниП(req);
globalThis.result={prompt:JSON.parse(req.текст),
 facts:{window:НАЛАШТУВАННЯ_РУШІЯ_П.qa.loaded_context_length,
 before:estimate(before)+4000,after:estimate(req.текст)+4000,reduced:req.скорочено}};`,ctx);
process.stdout.write(JSON.stringify(ctx.result));
"""
процес = subprocess.run(["node", "-e", код, str(корінь)],
                         input=json.dumps(дані, ensure_ascii=False),
                         capture_output=True, text=True, encoding="utf8", check=True)
вихід = json.loads(процес.stdout)
після = вихід["prompt"]
print(json.dumps(вихід["facts"], ensure_ascii=False))
print("ПІСЛЯ: кандидати", [р["n"] for р in next(iter(після["items"].values()))])
print("Рядків легенди:", len(next(iter(після["knowledge_legend"]["sections"].values()))["rows"]))
try:
    З.відновити(після)
except KeyError as помилка:
    assert помилка.args == ("lab",)
    print("ПІСЛЯ: KeyError: 'lab' — регресію відтворено")
else:
    raise AssertionError("Регресію не відтворено")
