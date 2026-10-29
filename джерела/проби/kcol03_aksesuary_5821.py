"""K-COL-03 картки (рядок 5821): заява про сім'ї схеми на великих речах на записі `живі_1083` (07 ПІСЛЯ, картка руки 1).
Друкує заяви `card_scheme`: чи сказано кодами, що лічились лише великі речі (`counted`), і яку відсутню сім'ю несе
аксесуар цієї ж картки (`on_accessories`). Запуск: python3 проби/kcol03_aksesuary_5821.py <вердикти.txt сцени 01 живі_1083> <каталог_повний.xml>
(тека — `git archive origin/claude/zhyvi-1083 аудит/живі_1083`; каталог — `gunzip -c каталог_повний.xml.gz`)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import palette as P

в = next(x for п in json.load(open(sys.argv[1], encoding="utf8"))["прогони"] for x in п["вердикти"]
         if str(x.get("рука")) == "1")
великі = next(y["етапи"]["суд"]["схема_жінці"]["великі"] for п in json.load(open(sys.argv[1], encoding="utf8"))["прогони"]
              for y in п["вердикти"] if ((y.get("етапи") or {}).get("суд") or {}).get("схема_жінці"))
речі = [dict(id=р["id"], слот=р["слот"]) for р in в["речі_образу"]]
import фід_каталог as F
кат = {r.get("id"): r for r in F._база_прогону(sys.argv[2], 0, sys.argv[3] if len(sys.argv) > 3 else "кеш_кольорів.json")["каталог"]}
за_ід = {р["id"]: кат.get(р["id"]) or {} for р in в["речі_образу"]}
спец = {"_схема": "тріада", "_поверхні": "великі", "_сім_ї": [dict(роль=с["роль"], дуга=с["дуга"]) for с in великі]}
пов = P.повідомлення_великих(речі, спец, за_ід, великі={"сім_ї": великі}, обрана="стилістка")
for з in (пов or {}).get("statements", []):
    print(з.get("code"), json.dumps(з.get("values") or {}, ensure_ascii=False))
заяви = {з.get("code"): з.get("values") or {} for з in (пов or {}).get("statements", [])}
к = заяви.get("big_items_carry_only_some") or {}
print("ПІДСУМОК: лічба лише великих кодом —", "так" if к.get("counted") else "ні",
      "· відсутня сім'я на аксесуарах —", к.get("on_accessories") or "не сказано")
