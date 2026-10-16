"""Рядок 5742, ЖИВИЙ ПІСЛЯ: 5 фраз її слів про перелік речей → мовна модель (хід `review_items_fix`, промпт продукту) → дії кодами → `виправити_речі`.
Вірна фраза — кінцевий перелік відповідає очікуваному (перевіряє код по полях, а не очі). Запуск (з теки джерела), ноутбук, MamayLM:
MODEL_URL=http://127.0.0.1:1234/v1 MODEL_MOVA=mamaylm-gemma-3-12b-it-v2.0 python ../аудит/проби/речі_голосом_живий_5742.py [тека ВИХІД]"""
import json, os, sys, time, urllib.request
sys.path.insert(0, os.getcwd()); sys.stdout.reconfigure(encoding="utf-8")
import оцінка_образу as О, мовний_шар as М
РЕЧІ = [dict(ід="ф1", фото="ф1", вид="blouse", назва="white blouse", слот="верх", колір="білий", в_образі=True),
        dict(ід="ф1·2", фото="ф1", вид="trousers", назва="black trousers", слот="низ", колір="чорний", в_образі=True),
        dict(ід="ф2", фото="ф2", вид="ankle_boots", назва="black ankle boots", слот="взуття", колір="чорний", в_образі=True),
        dict(ід="ф2·2", фото="ф2", вид="tote", назва="brown tote bag", слот="сумка", колір="коричневий", в_образі=True)]
є = lambda р, **к: any(all(х.get(п) == v for п, v in к.items()) for х in р)
ФРАЗИ = [("там не штани, а вершкові ботильйони, чорні — запасні", lambda р: not є(р, вид="trousers") and є(р, вид="ankle_boots", колір="вершковий", в_образі=True)
          and not є(р, вид="ankle_boots", колір="чорний", в_образі=True) and є(р, вид="ankle_boots", колір="чорний", в_образі=False)),
         ("сумки там нема, прибери її", lambda р: not є(р, слот="сумка") and len(р) == 3),
         ("блуза не біла, а бежева", lambda р: є(р, вид="blouse", колір="бежевий") and len(р) == 4),
         ("ще є сіра спідниця", lambda р: є(р, вид="skirt", колір="сірий") and len(р) == 5),
         ("чорні штани — це насправді джинси", lambda р: є(р, вид="jeans", слот="низ") and not є(р, вид="trousers") and len(р) == 4)]
тека = sys.argv[1] if len(sys.argv) > 1 else None; вірних = 0
for і, (слова, вірно) in enumerate(ФРАЗИ, 1):
    п = М.промпт_входу("review_items_fix", слова, {"items": О.речі_для_слів(РЕЧІ)}); т0 = time.time()
    з = urllib.request.Request(os.environ["MODEL_URL"].rstrip("/") + "/chat/completions", json.dumps(dict(model=os.environ["MODEL_MOVA"], temperature=0,
        max_tokens=1500, stream=False, messages=[dict(role="user", content=п)])).encode(), {"Content-Type": "application/json"})
    сире = json.load(urllib.request.urlopen(з, timeout=1800))["choices"][0]["message"].get("content") or ""
    пер = М.прийняти_вхід("review_items_fix", сире); дії = пер["внутрішня"].get("actions", []); в = О.виправити_речі(РЕЧІ, дії)
    ок = bool(вірно(в["речі"])); вірних += ок
    if тека: os.makedirs(тека, exist_ok=True); open(os.path.join(тека, "%02d.txt" % і), "w", encoding="utf-8").write(слова + "\n\n" + сире)
    print("%d %s «%s» · %.1f с\n   дії: %s\n   незнайомі: %s | речі: %s" % (і, "✔" if ок else "✘", слова, time.time() - т0, json.dumps(дії, ensure_ascii=False),
          пер["незнайомі"] + в["незнайомі"], [(р["ід"], р["вид"], р["колір"], р["в_образі"]) for р in в["речі"]]))
print("ВІРНИХ %d з %d (потрібно ≥ 4)" % (вірних, len(ФРАЗИ)))
