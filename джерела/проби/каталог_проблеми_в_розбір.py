# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «розбір MamayLM і коди мовної моделі». ФАКТ на
# трьох прогонах MamayLM еталону 60 речей (`аудит/розбір_каталогу/404_а*/розбір.json`, ті самі
# вхід і модель): (1) частка кодів «unknown» і «not_applicable»; (2) скільки полів однакові в
# усіх трьох прогонах — тобто наскільки код речі залежить від випадку, а не від тексту
# крамниці; (3) найнестійкіші поля. Вигадки проти еталону очима — `404_ПІДСУМОК.txt`.
import os, sys, json, collections as C
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
тека = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ТУТ, os.pardir, "аудит", "розбір_каталогу")

def пласко(d, п=""):
    """Відповідь розбору → {шлях поля: значення} без `features` (його міряє сусідня проба)."""
    for k, v in d.items():
        if k == "features":
            continue
        if isinstance(v, dict):
            yield from пласко(v, п + k + ".")
        else:
            yield п + k, json.dumps(sorted(json.dumps(x, sort_keys=True) for x in v)
                                if isinstance(v, list) else v, ensure_ascii=False)
прогони = [{r: dict(пласко(v)) for r, v in json.load(open(os.path.join(тека, п, "розбір.json"),
            encoding="utf-8")).items() if isinstance(v, dict)}
           for п in sorted(os.listdir(тека)) if os.path.exists(os.path.join(тека, п, "розбір.json"))]
вс = C.Counter(z for п in прогони for r in п.values() for z in r.values())
усього = sum(вс.values())
print("прогонів %d · кодів %d · unknown %.0f %% · not_applicable %.0f %%"
      % (len(прогони), усього, 100 * вс['"unknown"'] / усього, 100 * вс['"not_applicable"'] / усього))
однак, пар, поле_різне = 0, 0, C.Counter()
for r in set.intersection(*(set(п) for п in прогони)):
    for f in прогони[0][r]:
        пар += 1
        if len({п[r].get(f) for п in прогони}) == 1:
            однак += 1
        else:
            поле_різне[f] += 1
print("полів речі %d · однакові в усіх прогонах %d (%.0f %%)" % (пар, однак, 100 * однак / пар))
print("найнестійкіші поля (речей із розбіжністю):", dict(поле_різне.most_common(8)))
