"""Ґратка основ без слова в ключі (15885): чи кожна клітинка дуги `palettes.СІМ_Ї` × 5 смуг світлоти × 3 смуги хроми
(127 — та сама геометрія, що в `міст_основи.ґратка_основ`, без жодного злиття) є на ґратці. Клітинка «своя» — її hex
на ґратці; «злита» — у тій самій гамі є клітинка, якої око від неї не розрізняє (ΔE*ab ≤ JND `колір_тон`); інакше —
«зникла». Друкує: клітинок (кольорові, нейтралі, разом), hex, своїх/злитих/зниклих за дугами, пари однієї гами за
ΔE2000 і ΔE*ab (скільки ближче за пороги, найближчі), підписи чипів справжнім `основиПалітриП` у node (слово родини,
однакові підписи в гамі, без рядка таблиці) і відбиток складу ґратки. Працює й на дереві до правки (ключ зі словом).
Запуск із кореня дерева: python3 -W ignore <шлях>/вимір.py"""
import hashlib, itertools, json, math, subprocess, sys
from collections import defaultdict
sys.path.insert(0, "джерела")
import palettes as П, colorspace as cs, міст_основи as МО, словник_кольору as СК, колір_образу as КО  # noqa: E402
import verify as V, колір_тон as КТ  # noqa: E402
from колір_простір_перетворення import de00  # noqa: E402
JND = КТ.РЕЄСТР["поріг_помітності"]["val"]
осн, порядок = МО.ґратка_основ()
нейтр = [к for к in порядок if к.split("·")[1] == "нейтраль"]
print("ґратка: клітинок", len(порядок), "· кольорових", len(порядок) - len(нейтр), "· нейтралей", len(нейтр),
      "· hex", len({осн[к][0] for к in порядок}))
# ── усі клітинки дуг: та сама геометрія, без злиття ──
Llo, Lhi = МО.МЕЖІ_ПРОСТОРУ_L
Ls = [Llo + (Lhi - Llo) * (i + 0.5) / МО.СМУГ_L for i in range(МО.СМУГ_L)]
L_МІН = {"рожева": 55.0, "жовта": 45.0}
дуги = []
for сім, в in П.СІМ_Ї.items():
    for бік in ("тепла", "холодна"):
        д = в[бік]
        if not д:
            continue
        h, кл = П.середина_дуги(д), []
        for L in Ls:
            if L < L_МІН.get(сім, 0.0):
                continue
            ст, _ = cs.c_max_поверхня(L, h)
            верх = min(МО.МЕЖІ_ПРОСТОРУ_C[1], ст if ст else МО.МЕЖІ_ПРОСТОРУ_C[1], 2500.0 / max(L, 1e-6))
            if верх < МО.МЕЖІ_ПРОСТОРУ_C[0]:
                continue
            for і, см in enumerate(МО.СМУГИ_ХРОМИ):
                lab = П.lab_з_lch(L, МО.МЕЖІ_ПРОСТОРУ_C[0] + (верх - МО.МЕЖІ_ПРОСТОРУ_C[0]) * (і + 1) / 3, h)
                if not КО.нейтраль(lab):
                    кл.append(dict(hex=П.hex_з_lab(lab), см=см, L=round(L)))
        дуги.append((сім + " " + бік, кл))
на_ґратці = defaultdict(list)
for к in порядок:
    if к.split("·")[1] != "нейтраль":
        на_ґратці[к.split("·")[-1]].append(осн[к][0])
разом, злиті = defaultdict(int), []
for ім, кл in дуги:
    с = з = н = 0
    for к in кл:
        if к["hex"] in на_ґратці[к["см"]]:
            с += 1
        elif any(math.dist(cs.hx(к["hex"]), cs.hx(х)) <= JND for х in на_ґратці[к["см"]]):
            з += 1
            х = min(на_ґратці[к["см"]], key=lambda х: math.dist(cs.hx(к["hex"]), cs.hx(х)))
            злиті.append("%s L%d %s %s→%s ΔE2000 %.2f ΔE*ab %.2f" % (ім, к["L"], к["см"], к["hex"], х,
                                                                 de00(cs.hx(к["hex"]), cs.hx(х)), math.dist(cs.hx(к["hex"]), cs.hx(х))))
        else:
            н += 1
    разом["всіх"] += len(кл); разом["своїх"] += с; разом["злитих"] += з; разом["зниклих"] += н
    print("  дуга %-18s клітинок %2d · своїх %2d · злитих %2d · зниклих %2d" % (ім, len(кл), с, з, н))
print("клітинок дуг %(всіх)d: своїх %(своїх)d · злитих %(злитих)d · зниклих %(зниклих)d" % разом)
print("  злиті (клітинка → чип тієї самої гами):", "; ".join(злиті) or "—")
рож = [кл for ім, кл in дуги if ім.startswith("рожева")]
print("рожевих (тепла + холодна) своєю клітинкою:", sum(1 for кл in рож for к in кл if к["hex"] in на_ґратці[к["см"]]),
      "з", sum(len(кл) for кл in рож))
# ── пари однієї гами на ґратці ──
пари = []
for см, hx in на_ґратці.items():
    for a, b in itertools.combinations(hx, 2):
        пари.append((de00(cs.hx(a), cs.hx(b)), math.dist(cs.hx(a), cs.hx(b)), см, a, b))
пари.sort()
print("пар однієї гами: ΔE*ab ≤ JND %.1f: %d; ΔE2000 < 1: %d, < 2: %d, < 3: %d" % (
    JND, sum(1 for п in пари if п[1] <= JND), *(sum(1 for п in пари if п[0] < x) for x in (1, 2, 3))))
print("  найближчі:", "; ".join("%s %s–%s ΔE2000 %.2f ΔE*ab %.2f" % (п[2], п[3], п[4], п[0], п[1]) for п in пари[:4]))
# ── підписи чипів справжнім показом ──
сл_родини = {w for w in (dict((к, с) for к, с, _ in СК._ЗАПИСИ).get(к) for к in СК.КОД_СІМ_Ї_МОДУЛЯ.values()) if w}
клітинки = []
for к in порядок:
    hx, ім = осн[к]
    L, C, h = cs.lch(cs.hx(hx))
    в = П.відтінок(hx)
    клітинки.append(dict(ключ=к, hex=hx, назва=ім, бал=0, сім_я=None, осі=dict(Cstar=C, L=L), **({"відтінок": в} if в else {})))
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
гами = json.loads(subprocess.run(["node", "-e", JS], input=json.dumps(клітинки, ensure_ascii=False),
                                 capture_output=True, text=True, check=True).stdout)
усі = [x for г in гами.values() for x in г]
print("чипів (клітинка × гама):", len(усі), "· без рядка таблиці відтінків:", sum(1 for к in клітинки if "відтінок" not in к),
      "· підпис зі слова коду родини:", sum(1 for x in усі if x[2].split(" · ")[0].split(" ")[0] in сл_родини),
      "· однакових підписів у різних кольорів однієї гами:",
      sum(1 for г in гами.values() for м, h in (lambda d: d.items())(
          (lambda d: [d[x[2]].add(x[1]) for x in г] and d)(defaultdict(set))) if len(h) > 1))
print("відбиток складу ґратки (ключ, hex, назва по порядку):",
      hashlib.sha256(json.dumps([(к, осн[к][0], осн[к][1]) for к in порядок], ensure_ascii=False).encode()).hexdigest()[:16])
