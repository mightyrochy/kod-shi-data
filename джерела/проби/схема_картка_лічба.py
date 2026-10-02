# -*- coding: utf-8 -*-
"""СХЕМА-КАРТКА (рядки 1404, 1405, 1292): що картка рук 1–2 каже жінці про схему, і чи суд вимагає акценту.
По теках прогону стенда (`картки.txt`, `вердикти.txt.gz` чи `.txt`) друкує: картки рук 1–2; абзаци «вийшов
нейтральним» у шапці картки; з них неправдиві — у переліку картки є річ, яку крамниця зве тоном (`verify.слово_називає_тон`);
дії «не це» в абзаці і чи названа там річ стоїть у переліку; знахідки суду `scheme_promised_accent_all_neutral`
і `blandness_floor_not_reached`. Неправду з фото проба не бачить — картки читати очима.
Запуск: cd джерела && python3 проби/схема_картка_лічба.py <тека> [<тека> …]"""
import gzip, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import verify as V
ЦІНА = re.compile(r"·\s*[\d\s  ]+₴")
for тека in sys.argv[1:]:
    к = open(os.path.join(тека, "картки.txt"), encoding="utf-8").read()
    карток = нейтр = неправда = дій = назва_є = 0
    for блок in re.split(r"═══ картка ", к)[1:]:
        if not re.match(r"\d+ з \d+ · рука [12] ", блок):
            continue
        карток += 1
        рядки = блок.split("\n")
        речі = [рядки[і - 1].strip() for і, р in enumerate(рядки) if і and ЦІНА.search(р)]
        шапка = рядки[:next((і - 1 for і, р in enumerate(рядки) if і and ЦІНА.search(р)), len(рядки))]
        абз = [р for р in шапка if len(р) > 60 and re.search(r"схем|[Пп]алітр", р) and "нейтральн" in р]
        if абз:
            нейтр += 1
            if any(V.слово_називає_тон(V.назва_кольору(н) or "") for н in речі):
                неправда += 1
        for р in абз:
            if re.search(r"[Нн]е ц[еяю]", р):
                дій += 1
                назва_є += any(f"«{н}»" in р or f"„{н}“" in р for н in речі)
    вп = os.path.join(тека, "вердикти.txt.gz")
    в = (gzip.open(вп, "rt", encoding="utf-8") if os.path.exists(вп) else
         open(os.path.join(тека, "вердикти.txt"), encoding="utf-8")).read()
    print("%s: карток рук 1–2 %d · «вийшов нейтральним» %d (неправда за словом %d) · «не це» %d (назва з переліку %d)"
          " · суд: all_neutral %d, blandness %d" % (os.path.basename(тека.rstrip("/")), карток, нейтр, неправда, дій,
          назва_є, в.count('"scheme_promised_accent_all_neutral"'), в.count('"blandness_floor_not_reached"')))
