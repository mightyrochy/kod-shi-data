"""Між «Записати вердикт» і рядком у IndexedDB стоїть виклик моделі без сітки.

`зап.onclick = ()=>записати(поз)` не ловить відмови: `записати` — async, і все,
що кинуло ДО останнього try, лишає жінку без вердикта й БЕЗ ЖОДНОГО слова
(кнопка лишається активною, статус завмирає на «Стилістка читає твій коментар…»).
Друкує кожен `await` тіла `записати` і чи він у try/catch.
"""
import pathlib
import re

КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
рядки = (КОРІНЬ / "джерела" / "показ.html").read_text(encoding="utf-8").splitlines()
поч = next(i for i, р in enumerate(рядки) if "async function записати(поз)" in р)
кін = next(i for i, р in enumerate(рядки) if i > поч and р.startswith("}"))

глибина = 0
for i in range(поч, кін):
    р = рядки[i]
    гола = re.sub(r"/\*.*?\*/", "", р)
    if re.search(r"^\s*\}?\s*catch\b", гола):
        глибина -= 1
    було = глибина or ("try{" in гола)
    if re.search(r"\btry\s*\{", гола):
        глибина += 1
    if "await " in гола:
        що = re.search(r"await\s+([A-Za-zА-Яа-яІіЇїЄєҐґ_$][\w$А-Яа-яІіЇїЄєҐґ.]*)", гола)
        print("   %s показ.html:%d await %s"
              % ("у try " if було else "БЕЗ try", i + 1, (що.group(1) if що else "?")))

тіло = "\n".join(рядки[поч:кін])
print("тіло `записати`: рядків", кін - поч, "· try", тіло.count("try{"),
      "· записів у сховище", тіло.count("'вердикти','readwrite'"),
      "· повідомлень жінці про невдачу", тіло.count("Не записалось"))
клік = [р for р in рядки if "зап.onclick" in р]
print("прив'язка кнопки:", клік[0].strip() if клік else "?",
      "· ловить відмову:", "так" if клік and ".catch" in клік[0] else "НІ")
