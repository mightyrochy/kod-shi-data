# Робить аудит/проби/рв6_н3_час.js — копію стенда з одним доданим рядком: годинник збору (ЧАСИ.звіт) перед записом стану N2.
# Без нього гілка N2 кінчається раніше за звіт, і CHASY_OUT не пишеться. Код продукту не міняється.
import pathlib, sys
к = pathlib.Path(__file__).resolve().parents[2] / 'проби'
s = (к / 'рв6_н3.js').read_text(encoding='utf8')
мітка = "    fs.writeFileSync(process.env.N2_STAN, JSON.stringify(стан, null, 1));"
assert s.count(мітка) == 1, s.count(мітка)
s = s.replace(мітка, "    try { await ЧАСИ.звіт(стор); } catch (е) { console.log('ЧАСИ звіт не вийшов: ' + е); }\n" + мітка)
клік = "  if (!збиранняЗЧату) await стор.click(ПАРА ? '#mirror-work [data-ux=\"pair-build\"]' : '#зб-зібрати', { noWaitAfter: true });"
assert s.count(клік) == 1, s.count(клік)
s = s.replace(клік, "  console.log('КЛІК_МС ' + Date.now());\n" + клік)
(к / 'рв6_н3_час.js').write_text(s, encoding='utf8')
# Варіант пункту 3: додатково `&межа=<симв.>` у посиланні (читає лише стендова збірка, `варіант.py`)
гот = "(process.env.VIKNO_N2 ? '&вікно=' + process.env.VIKNO_N2 : '')"
assert s.count(гот) == 1, s.count(гот)
s = s.replace(гот, гот + " + (process.env.MEZHA ? '&межа=' + process.env.MEZHA : '')")
(к / 'рв6_н3_час_вар.js').write_text(s, encoding='utf8'); print('ok')
