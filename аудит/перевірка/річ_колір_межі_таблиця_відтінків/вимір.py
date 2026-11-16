"""Назва відтінку на чипі основи (15506, 15683): підписи клітинок ґратки основ так, як їх складає показ
(`показ/палітра.js`, `основиПалітриП` — справжня функція в node, з тими самими клітинками в кожній гамі).
`--до` — клітинки без поля `відтінок` (як на `main`, де його нема). Друкує: клітинок і кольорів (hex), підписів зі
словом родини (основа підпису — `palettes.назва` з `назва_як` «сім'я»; і будь-яке слово коду сім'ї модуля), клітинок
без рядка таблиці, однакових підписів у різних кольорів однієї гами (з парами), клітинки стику 15683 і відбиток складу
ґратки. Запуск із кореня дерева: python3 -W ignore <шлях>/вимір.py [--до]"""
import hashlib, json, subprocess, sys
from collections import defaultdict
sys.path.insert(0, "джерела")
import palettes as П, colorspace as cs, міст_основи as МО, словник_кольору as СК  # noqa: E402
ДО = "--до" in sys.argv
осн, порядок = МО.ґратка_основ()
сл_родини = {w for w in (dict((к, с) for к, с, _ in СК._ЗАПИСИ).get(к) for к in СК.КОД_СІМ_Ї_МОДУЛЯ.values()) if w}
клітинки = []
for к in порядок:
    hx, ім = осн[к]
    L, C, h = cs.lch(cs.hx(hx))
    в = None if ДО else (П.відтінок(hx) if hasattr(П, "відтінок") else None)
    клітинки.append(dict(ключ=к, hex=hx, назва=ім, бал=0, сім_я=None, осі=dict(Cstar=C, L=L),
                         **({"відтінок": в} if в else {})))
JS = r"""
const fs = require('fs'), vm = require('vm');
const кл = JSON.parse(fs.readFileSync(0, 'utf8'));
const ctx = {ПАЛІТРА: {основи: {кольори: кл, нейтралі: [], інші: []}}, ВИБІР: {смуга: null},
             ДОВІДНИК: {показ: {температура_словом: {тепла: 'теплий', холодна: 'холодний', нейтраль: 'нейтральний'},
                                СІМ_Ї_ПОРЯДОК: []}}, console};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('джерела/показ/палітра.js', 'utf8'), ctx);
const вих = {};
for (const г of ['приглушені', 'середні', 'насичені']){
  ctx.ВИБІР.смуга = г;
  const о = vm.runInContext('основиПалітриП()', ctx);
  вих[г] = [...о.рек, ...о.інші].map(x => [x.ключ, x.hex, x.мітка]);
}
process.stdout.write(JSON.stringify(вих));
"""
р = subprocess.run(["node", "-e", JS], input=json.dumps(клітинки, ensure_ascii=False), capture_output=True,
                   text=True, check=True)
гами = json.loads(р.stdout)
як = {к["hex"]: П.назва(cs.hx(к["hex"]))[1] for к in клітинки}
print("ДО (без поля `відтінок`)" if ДО else "ПІСЛЯ")
print("ґратка: клітинок", len(клітинки), "· кольорів (hex)", len({к["hex"] for к in клітинки}),
      "· без рядка таблиці", sum(1 for к in клітинки if "відтінок" not in к))
усі = [x for г in гами.values() for x in г]
основа = lambda x: x[2].split(" · ")[0]
print("чипів (клітинка × гама):", len(усі),
      "· основа підпису — слово родини `назва_як` «сім'я»:",
      sum(1 for x in усі if як[x[1]] == "сім'я" and основа(x).split(" ")[0] == осн[x[0]][1]),
      "· клітинок із такою основою:",
      len({x[0] for x in усі if як[x[1]] == "сім'я" and основа(x).split(" ")[0] == осн[x[0]][1]}),
      "· основа підпису — слово коду сім'ї модуля (будь-яке `назва_як`):",
      len({x[0] for x in усі if основа(x).split(" ")[0] in сл_родини}))
for г, ряд in гами.items():
    за_міткою = defaultdict(set)
    for _, hx, м in ряд:
        за_міткою[м].add(hx)
    одн = {м: sorted(h) for м, h in за_міткою.items() if len(h) > 1}
    print("гама %s: чипів %d, кольорів %d, однакових підписів у різних кольорів: %d (кольорів %d)%s" % (
        г, len(ряд), len({x[1] for x in ряд}), len(одн), sum(len(h) for h in одн.values()),
        "".join("\n    «%s»: %s" % (м, ", ".join(h)) for м, h in sorted(одн.items()))))
for hx in ("#dbd8be", "#dcd9b0"):
    print("стик 15683", hx, "→", sorted({x[2] for x in усі if x[1] == hx}))
print("відбиток складу ґратки (ключ, hex, назва по порядку):",
      hashlib.sha256(json.dumps([(к, осн[к][0], осн[к][1]) for к in порядок], ensure_ascii=False).encode()).hexdigest()[:16])
print("підписи:", "; ".join("%s %s" % (x[1], x[2]) for x in гами["середні"]))
