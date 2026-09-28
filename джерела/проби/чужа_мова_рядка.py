# -*- coding: utf-8 -*-
"""ПРОБА рядка 212 (Ч-7, доповнення менеджера 28.09.2026): сторож `чужоюМовоюП` ловить
МІШАНИЙ рядок — англійську прозу з українськими словами з даних усередині, — якого стара
перевірка «всі літери латинські» пропускала. Рядки з перевірки #436: те, що бачила жінка на
картці 4 і на «Палітрі»; той самий рядок на main; звичайний рядок із назвою крамниці, який
знімати НЕ можна. ДРУКУЄ вердикт старої і нової перевірки.
ЗАПУСК (тека `джерела`): python3 проби/чужа_мова_рядка.py"""
import io, json, os, re, subprocess, sys

ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
КОД = io.open(os.path.join(ТУТ, "показ.html"), encoding="utf-8").read()
ШМАТКИ = [re.search(р, КОД, re.S).group(0) for р in (
    r"const ЧАСТКА_ЧУЖОЇ_П = [\d.]+;",
    r"function словаП\(т\)\{.*?\n\}",
    r"function латинськеСловоП\(с\)\{.*?\n\}",
    r"function чужоюМовоюП\(т, свої\)\{.*?\n\}")]
РЯДКИ = [("ехо англійського визначення (картка 4 і «Палітра» цієї голови)",
          "the stylist chose this outfit's palette scheme for her — аналогова; the scheme rests on "
          "a colour; the colour was to be carried by these slots — сумка, пояс; but this outfit "
          "came out all neutral"),
         ("той самий рядок на main (українською)",
          "схему палітри для цього образу обрала за тебе стилістка — аналогова; схема тримається "
          "на кольорі; колір мали нести речі на таких місцях — сумка, пояс; а цей образ вийшов "
          "увесь нейтральний"),
         ("звичайний рядок картки з назвою крамниці й бренда",
          "Берет Bloom із зеленими акцентами чорний від honchstudio — у твоїй палітрі")]
ЖС = "\n".join(ШМАТКИ) + """
const стара = т => { const л = String(т||'').match(/\\p{L}/gu) || [];
  return л.length > 0 && л.every(x => /\\p{Script=Latin}/u.test(x)); };
for (const [чому, т] of JSON.parse(process.argv[1]))
  console.log(JSON.stringify([чому, стара(т), чужоюМовоюП(т)]));
"""
п = subprocess.run([ "node", "-e", ЖС, json.dumps(РЯДКИ, ensure_ascii=False)],
                   capture_output=True, text=True, encoding="utf-8")
if п.returncode:
    print("node впав:", (п.stderr or "")[-300:]); sys.exit(1)
for р in п.stdout.strip().splitlines():
    чому, стара, нова = json.loads(р)
    print("%-62s стара знімає: %-5s нова знімає: %s" % (чому[:62], стара, нова))
print("ФАКТ: мішаний англійський рядок стара перевірка пропускала, нова знімає")
