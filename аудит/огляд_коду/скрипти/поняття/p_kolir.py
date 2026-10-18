"""Розходження вікон кольору: (1) дуга очей — пул/вікна палітри (CIELAB, запас 10°) проти суду (сім'я очей, коло) і
проти `у_дугах_кола`; (2) ролі схем — CIELAB +10° проти ±15° кола; (3) сітка LCh. Запуск: cd wt/джерела && python3 p_kolir.py"""
import json, glob, sys, collections as K, time; sys.path.insert(0, ".")
import bridge as B, colorspace as cs, стенд_знімок as СЗ, колір_річ as КР, колір_відношення as КВ, palettes as ПЛ, палітра_схеми as ПС
t0=time.time()
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); пул=set()
for назва in ("офіс·18°C", "дощ·ресторан·вечір", "весілля·гість", "спека·парк"):
    к = json.loads(B.виклик("запити", json.dumps(dict(вх0, сценарій=dict(СЗ.СЦЕНАРІЇ[назва]), випадок=назва), ensure_ascii=False)))["кандидати"]
    пул |= {r["id"] for xs in к.values() for r in xs}
кат_все = B.каталог_останнього_пакета()
кат_повний = [r for r in кат_все if КР.межі_кольору(r) and КР.нейтраль_меж(r) == "ні"]
import random; кат = sorted(кат_повний, key=lambda r: str(r["id"])); random.Random(7).shuffle(кат); кат = кат[:2000]
print("кольорових у каталозі всього", len(кат_повний), "; вибірка (сід 7)", len(кат), flush=True)
print("каталог %d, кольорових %d, пул руки 1 (4 сцени) %d, кольорових у пулі %d; %.0fs" % (len(кат_все), len(кат), len(пул), sum(x["id"] in пул for x in кат), time.time()-t0))
очі = [вх0["очі"]] + [json.load(open(f, encoding="utf-8"))["eyes"] for f in sorted(glob.glob("/home/user/kod-shi-data/аудит/проби/жінки/ж*.json"))]
b = lambda v: {"так":"т","ні":"н","невідомо":"?"}.get(v, "-") if not isinstance(v,(bool,type(None))) or v is None else ("т" if v else "н")
L = K.Counter()
for о in очі:
    h = cs.lch(cs.hx(о))[2]; д = ПЛ.дуга_очей(h); зо = КР.запис_кольору(dict(lab=cs.hx(о)))
    for x in кат:
        вид = "слово" if КР.не_вимір(x) else "вимір"
        A = КР.у_дугах_меж(x, [д], 10.0)             # пул/вікна K-PAL-09/10/14
        Bc = КР.у_дугах_кола(x, [д], до_кінця_згасання=True)  # коло зі згасанням (рядок 4781)
        C = КР.у_сім_ї_очей(x, зо)                    # суд K-PAL-02/13, основи
        D = КР.несе_тон(x, д) is not None             # міст_пакет / суд_ремесло носії тону
        for де in ("кат",) + (("пул",) if x["id"] in пул else ()):
            L[("очі", де, вид, "A/B", b(A)+b(Bc))]+=1
            L[("очі", де, вид, "A/C", b(A)+b(C))]+=1
            L[("очі", де, вид, "A/D", b(A)+("т" if D else "н"))]+=1
            L[("очі", де, "усі", "n", "")]+=1
print("очі готово %.0fs" % (time.time()-t0), flush=True)
for i in range(12):
    for сх, з in ПС.СХЕМИ.items():
        for д in {tuple(д) for р, д in з["тон"](cs.з_кола_художника(30.0*i)).items() if isinstance(д, tuple)}:
            ц = (д[0] + ((д[1]-д[0]) % 360)/2) % 360
            дк = [cs.дуга_кола(ц, КВ.ДУГА_ВІДЛУННЯ)]
            for x in кат:
                вид = "слово" if КР.не_вимір(x) else "вимір"
                A = КР.у_дугах_меж(x, [д], 10.0); Bk = КР.у_дугах_кола(x, дк, до_кінця_згасання=True); B5 = КР.у_дугах_кола(x, дк)
                L[("ролі", "кат", вид, "A/Bkінець", b(A)+b(Bk))]+=1
                L[("ролі", "кат", вид, "A/B0.5", b(A)+b(B5))]+=1
json.dump({"|".join(k): v for k, v in L.items()}, open(sys.argv[1], "w"), ensure_ascii=False, indent=0)
for k, n in sorted(L.items()): print("  %-5s %-4s %-6s %-10s %-3s %8d" % (*k, n))
print("%.0fs" % (time.time()-t0))
