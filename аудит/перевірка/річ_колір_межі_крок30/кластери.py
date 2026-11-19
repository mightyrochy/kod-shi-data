"""Кластери кадру ювелірних речей із кодом металу: слово моделі зору й тон металу за вікном (дерево до кроку 29)."""
import sys, collections
sys.path.insert(0, "джерела")
import palettes as П, фід_каталог as ФК, фід_збагачення as FZ, colorspace as cs  # noqa
зб = FZ.читати_збагачення()
кат = ФК.прочитати_каталог(ФК.каталог_на_диску("каталог_повний.xml"), 0)["каталог"]
пари = collections.Counter(); прикл = collections.defaultdict(list)
for р in кат:
    if not (р.get("метал") and П.слот_металу(р.get("слот"), р.get("тип"))): continue
    z = зб.get(р.get("id")) or {}
    if not FZ.збагачення_придатне(z) or (z.get("версія") or 1) < 2: continue
    сл, lab, _ = FZ.колір_збагачення(z)
    кл = [(сл, lab)] if lab is not None else []
    д = FZ.другий_колір(z.get("колір_другий"))
    if д and д[1] is not None: кл.append((д[0], д[1]))
    for с, л in кл:
        в = П.метал_речі(tuple(л), р.get("слот"))
        L, C, h = cs.lch(tuple(л))
        пари[(с, в)] += 1
        if len(прикл[(с, в)]) < 3: прикл[(с, в)].append(f"{р['id']} {р.get('метал')} L{L:.0f} C{C:.0f} h{h:.0f}")
for (с, в), n in пари.most_common():
    print(f"слово моделі «{с}» · вікно {в}: {n} — {'; '.join(прикл[(с, в)])}")
