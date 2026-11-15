# Вироки п.4 на фікстурах: python3 порівняти_волосся.py <тека джерел>
import sys, json, os
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d); os.chdir(d)
import colorspace as cs, face_contrast as KC, face_features as FF, palettes as PL, суд_чеклісти as СЧ
def F_hex(hair, source="uncontrolled"):
    F = cs.features(cs.hx("#e8c4a8"), cs.hx(hair[0]), cs.hx("#5a7a8a"), джерело=source)
    for i, h in enumerate(hair[1:], start=2):
        F = cs.перерахувати_рису(F, "волосся_%d" % i, cs.hx(h), kind="волосся")
    F["_meta"]["protocol"] = source
    return F
випадки = {
  "один голос, мідне": F_hex(["#8a4a2a"]),
  "мідна й світла половини": F_hex(["#8a4a2a", "#e0c890"]),
  "сиве пасмо + темне": F_hex(["#3a2a20", "#b0b0b0"]),
  "один сивий голос": F_hex(["#a8a8a8"]),
  "маска: смуга + маса": None,
  "model_hex два голоси": F_hex(["#8a4a2a", "#e0c890"], "model_hex"),
}
Fm = F_hex(["#3a2a20"]); Fm = cs.перерахувати_рису(Fm, "волосся_біля_обличчя", cs.hx("#c8a070"), kind="волосся")
Fm["_meta"]["вхід"] = "zones"; випадки["маска: смуга + маса"] = Fm
for н, F in випадки.items():
    src = F["_meta"]["protocol"]
    к = FF._контраст(F, src)
    д = KC.домінантність(F, 0.35)
    try:
        чк = СЧ.входи_палітри(F, src) if hasattr(СЧ, "входи_палітри") else None
    except Exception as e:
        чк = {"помилка": repr(e)[:80]}
    print(json.dumps(dict(випадок=н, value_обличчя=None if KC.value_обличчя(F) is None else round(KC.value_обличчя(F),1),
        контраст=(к.get("доступно"), к.get("рівень"), к.get("value_gap"), к.get("внутрішній_розкид_волосся")),
        рис=(FF._контраст_рис(F) or {}).get("M"), домінантність=(д["рід"], д.get("власна_хрома")),
        ясність=None if PL.ясність_рис(F) is None else round(PL.ясність_рис(F),3),
        сивий=PL._сивий_біля_обличчя(F) if hasattr(PL, "_сивий_біля_обличчя") else "—"), ensure_ascii=False))
