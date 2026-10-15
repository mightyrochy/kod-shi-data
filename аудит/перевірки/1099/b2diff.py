import sys, json; sys.path.insert(0,"."); import bridge as B
sys.path.insert(0,".")
БОКИ=("надлишок","прісність","палітра","аксесуари")
д=json.load(open(sys.argv[1],encoding="utf-8")); вп=д["спільне"]["вхід_прогону"]; к=вп["колір"]; пас=д["спільне"]["паспорт"]
вх=dict(json.load(open("стенд_вх.json",encoding="utf-8")),зріст=вп["мірки"]["зріст"],обхвати=вп["мірки"]["обхвати"],шкіра=к["шкіра"][0],волосся=к["волосся"],очі=к["очі"],драп=вп["драп"],паспорт=пас,випадок=пас.get("подія") or "",сценарій=dict(вп["сценарій"],**{п_:пас[п_] for п_ in ("мета","намір") if пас.get(п_) not in (None,"невідомо")}))
B.виклик("запити",json.dumps(вх,ensure_ascii=False))
out={}
for в in (в for в in д["прогони"][0]["вердикти"] if str(в["рука"])=="1"):
    чр=json.loads(B.виклик("від_моделі",json.dumps(dict(вх,ід=[р["id"] for р in в["етапи"]["суд"]["речі"]]),ensure_ascii=False)))["чеклісти"]
    for б in БОКИ:
        for х in чр.get(б) or []: out[б+":"+str(х.get("пункт"))+"@"+str(в["позиція"])]=(х.get("стан"),str(х.get("чому"))[:50],str(х.get("бракує"))[:200])
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False)
