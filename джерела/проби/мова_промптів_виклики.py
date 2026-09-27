# -*- coding: utf-8 -*-
"""Ч-3 (CLAUDE.md п.12): МОВА ПРОМПТІВ ФУНКЦІОНАЛЬНОЇ МОДЕЛІ ПО ВИКЛИКАХ. Дві лічби, обидві
факт, без тлумачення. (1) Оголошення збирача в модулях продукту: шаблон `мова_промпту` і
кириличні слова в текстах ролі, входу, правил і підписів виходу. (2) Виклики моделі в
`показ.html` (`модельП`, `модельПРуки`, `модельП_блоки`): промпт зібрано в Python (поле
пакета) чи складено в JS (стала показу — тоді збирач його не бачить). Запуск із `джерела`:
python3 проби/мова_промптів_виклики.py"""
import importlib, io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import status, збирач_промптів as ЗП
КИР = re.compile(r"[а-яіїєґ]{3,}", re.I)
ог = []
for м in sorted(status.МОДУЛІ_ПРОДУКТУ):
    try:
        мод = importlib.import_module(м)
    except Exception as e:
        print("  НЕ ІМПОРТУВАВСЯ %s (%s)" % (м, type(e).__name__)); continue
    for л in (getattr(мод, "_фото_речей", None),):      # ліниве оголошення `річ_з_фото`
        if callable(л):
            л()
    for ім, в in sorted(vars(мод).items()):
        пари = [(ім, в)] if isinstance(в, ЗП.Оголошення) else (
            [("%s[%s]" % (ім, k), x) for k, x in в.items() if isinstance(x, ЗП.Оголошення)]
            if isinstance(в, dict) else [])
        ог += [(м, i, о) for i, о in пари]
print("оголошень збирача в модулях продукту: %d" % len(ог))
for м, ім, о in ог:
    т = [о.роль] + list(о.правила) + [" ".join((п.що, п.як, п.без)) for п in о.вхід] + list(о.поля_виходу.values())
    сл = sorted({w.lower() for x in т for w in КИР.findall(str(x))})
    print("  %-18s %-16s шаблон=%-3s кирил_слів=%-4d %s"
          % (м, ім, о.мова_промпту, len(сл), (", ".join(сл[:6]) + ("…" if len(сл) > 6 else "")) if сл else ""))
print("шаблон англійською: %d · українською: %d · з кирилицею в текстах: %d"
      % (sum(о.мова_промпту == "en" for _, _, о in ог), sum(о.мова_промпту != "en" for _, _, о in ог),
         sum(bool(КИР.search(" ".join([о.роль] + list(о.правила) + [п.що + п.як + п.без for п in о.вхід]))) for _, _, о in ог)))
Н = io.open("показ.html", encoding="utf-8").read()
ВИКЛ = re.compile(r"модельП(?:Руки|_блоки)?\(\s*([^,()]*(?:\([^()]*\))?[^,()]*)")
стала = re.compile(r"^[А-ЯЄІЇҐ_]{3,}$")
виклики = [в.strip() for в in ВИКЛ.findall(Н) if в.strip() and "промпт" not in в[:1]]
з_js = [в for в in виклики if стала.match(в.split("[")[0].strip())]
print("виклики моделі в показ.html: %d · промпт сталою JS (поза збирачем): %d %s"
      % (len(виклики), len(з_js), sorted(set(з_js)) or "—"))
