"""Е2-межі п.4 · записані відповіді живих прогонів на чотирьох межах (речі з фото, речі оцінки, вибір палітри, оцінка)
читає реєстр (`СхемаВідповіді.прочитати`) — версія коду з теки першого аргументу (`main` чи голова) → JSON лічби.
Запуск: python3 -I межа_записів.py <тека джерел> <файл переліку записів> → прочитано / латкою / розбіжність (повтор)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[1])
os.chdir(sys.argv[1])
import схема_відповіді as С
ЛАТКИ = ("answer_envelope_unwrapped", "task_label_unwrapped", "form_repaired")
лічба = {}
for шлях in open(sys.argv[2], encoding="utf8").read().split():
    т = open(шлях, encoding="utf8", errors="replace").read()
    г = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^\n]*)\) ──\n(.*)\n$", т, re.S)
    if not г or "HTTP 200" not in г.group(2) and "HTTP" in г.group(2):
        continue
    п, в = г.group(1), г.group(3)
    форма = ("РЕЧІ_З_ФОТО" if '"PHOTO_ITEMS"' in п and "her_items_in_words" in п else
             "РЕЧІ_ОЦІНКИ" if '"PHOTO_ITEMS"' in п else "ВИБІР_ПАЛІТРИ" if '"PALETTE_CHOICE"' in п else
             "OUTFIT_REVIEW_V1" if '"answer_schema"' in п and '"verdict"' in п and '"works"' in п else None)
    if not форма:
        continue
    треба = {}
    if форма == "ВИБІР_ПАЛІТРИ" and "треба" in С.СхемаВідповіді.прочитати.__code__.co_varnames:
        # що вона лишила стилістці — з входу промпту: схеми й основи є в «input», коли їх лишено
        вх = п
        треба = dict(треба=tuple(к for к, ключ in (("scheme", '"schemes"'), ("base", '"bases"')) if ключ in вх))
    об, причина, нотатки = С.СХЕМИ_ВІДПОВІДІ[форма].прочитати(в, **треба)
    л = лічба.setdefault(форма, dict(записів=0, прочитано=0, латкою=0, розбіжність=0, причини={}))
    л["записів"] += 1
    if об is None:
        л["розбіжність"] += 1
        к = re.sub(r"\[\d+\]", "[]", str(причина))[:120]
        л["причини"][к] = л["причини"].get(к, 0) + 1
    else:
        л["прочитано"] += 1
        л["латкою"] += any(str(н).startswith(ЛАТКИ) for н in (нотатки or []))
print(json.dumps(лічба, ensure_ascii=False, indent=1))
