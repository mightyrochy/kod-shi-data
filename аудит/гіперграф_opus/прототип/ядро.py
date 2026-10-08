# -*- coding: utf-8 -*-
"""ЯДРО ПРОТОТИПУ: типізований рольовий гіперграф образу з тризначними вердиктами.

Дослідницький прототип до записки `аудит/гіперграф_opus/ЗАПИСКА.md` (база e70c3c3).
НЕ продуктовий код і не пропозиція переписати продукт дослівно: він показує, що
схема з записки обчислювана, локальна й перевірна. Без залежностей і без імпорту
продуктових модулів — працює однаково в CPython 3.10+ і в Pyodide 0.26.

Ідентифікатори й коди — внутрішня мова (CLAUDE.md п.12): модуль не пише фраз людині.

Головні рішення (обґрунтування — записка §3–§4):
  * вершини — речі, особа, нагода; речі несуть ІНТЕРВАЛИ з джерелом, невідоме = None;
  * гіперребро = екземпляр шаблону правила з РОЛЬОВОЮ інцидентністю (роль → річ);
  * вимір правила — у власних одиницях (ΔE, см, кроки шкали, кількість), не «сила»;
  * вердикт — інтервальне порівняння з СМУГОЮ порогу: OK/BORDER/VIOLATE для
    обмежень, SUPPORT/BORDER/ABSENT для позитивних взаємодій, UNKNOWN (бракує
    входу) і NA (не застосовне) — окремо; відсутність ребра ≠ «перевірено»;
  * між правилами нічого не сумується: порівняння варіантів — лексикографічно за
    класами (PERSONAL > PHYSICAL > CONTEXTUAL > STYLISTIC > EXPRESSIVE) і Парето;
  * шар інтерпретації (позиція стилістки) і вибір людини — окремі записи, які не
    міняють виміру, лише дію над ним.
"""
from __future__ import annotations

import itertools

# ── ВЕРДИКТИ ────────────────────────────────────────────────────────────────
OK, BORDER, VIOLATE = "OK", "BORDER", "VIOLATE"        # обмеження
SUPPORT, ABSENT = "SUPPORT", "ABSENT"                    # позитивна взаємодія
UNKNOWN, NA = "UNKNOWN", "NA"                            # бракує входу / не застосовне

# Класи доменів — порядок = пріоритет у лексикографічному порівнянні варіантів.
CLASSES = ("PERSONAL", "PHYSICAL", "CONTEXTUAL", "STYLISTIC", "EXPRESSIVE")

# Позиції шару інтерпретації (стилістка) і вибору (людина).
DELIBERATE_BREAK, PERSON_CHOICE = "DELIBERATE_BREAK", "PERSON_CHOICE"
STANCE_OK, STANCE_REJECTED, STANCE_VOID, STANCE_ORPHANED = "ACCEPTED", "REJECTED", "VOID", "ORPHANED"


# ── ІНТЕРВАЛ ІЗ ДЖЕРЕЛОМ ────────────────────────────────────────────────────
class Iv:
    """Замкнений інтервал [lo, hi] з джерелом (`src`). Точка: lo == hi.

    Інтервал — це ЕПІСТЕМІЧНА межа (що ми знаємо про величину), не розподіл:
    ймовірнісного змісту він не несе."""
    __slots__ = ("lo", "hi", "src")

    def __init__(self, lo, hi=None, src=""):
        hi = lo if hi is None else hi
        if hi < lo:
            lo, hi = hi, lo
        self.lo, self.hi, self.src = float(lo), float(hi), src

    def __repr__(self):
        return ("%g" % self.lo) if self.lo == self.hi else ("[%g,%g]" % (self.lo, self.hi))

    def __add__(self, o):
        o = o if isinstance(o, Iv) else Iv(o)
        return Iv(self.lo + o.lo, self.hi + o.hi)

    def __sub__(self, o):
        o = o if isinstance(o, Iv) else Iv(o)
        return Iv(self.lo - o.hi, self.hi - o.lo)

    def mul(self, k):
        return Iv(self.lo * k, self.hi * k)

    def abs(self):
        if self.lo >= 0:
            return Iv(self.lo, self.hi)
        if self.hi <= 0:
            return Iv(-self.hi, -self.lo)
        return Iv(0.0, max(-self.lo, self.hi))

    def width(self):
        return self.hi - self.lo


def iv_max(ivs):
    """Інтервал максимуму набору інтервалів (точна межа)."""
    return Iv(max(i.lo for i in ivs), max(i.hi for i in ivs))


def iv_min(ivs):
    return Iv(min(i.lo for i in ivs), min(i.hi for i in ivs))


def hue_dist(a, b):
    """Кругова відстань тонів (градуси, 0–180) між ДУГАМИ a=[lo,hi] і b=[lo,hi].

    Точно для дуг шириною < 180°: мінімум — 0, якщо дуги перетинаються, інакше
    найближчі кінці; максимум — 180, якщо одна дуга містить антипод точки іншої,
    інакше найдальші кінці (відстань кусково-лінійна по кожному аргументу)."""
    def d(x, y):
        z = abs((x - y) % 360.0)
        return min(z, 360.0 - z)

    def inside(x, arc):
        return ((x - arc.lo) % 360.0) <= (arc.hi - arc.lo) + 1e-9

    ends = [d(x, y) for x in (a.lo, a.hi) for y in (b.lo, b.hi)]
    overlap = inside(a.lo, b) or inside(a.hi, b) or inside(b.lo, a) or inside(b.hi, a)
    anti = Iv((b.lo + 180.0) % 360.0, (b.lo + 180.0) % 360.0 + (b.hi - b.lo))
    antip = inside(a.lo, anti) or inside(a.hi, anti) or inside(anti.lo, a) or inside((anti.hi % 360.0), a)
    return Iv(0.0 if overlap else min(ends), 180.0 if antip else max(ends))


def box_dist(a, b):
    """Евклідова відстань між двома «коробками» в CIELAB (ΔE76) як інтервал.

    a, b — словники {"L": Iv, "a": Iv, "b": Iv}. Мінімум і максимум точні для
    коробок. ΔE76 — наближення перцептивної різниці (CIEDE2000 точніший), і це
    названо в записці; перцептивну метрику міняє один рядок."""
    lo2 = hi2 = 0.0
    for k in ("L", "a", "b"):
        x, y = a[k], b[k]
        gap = max(0.0, max(x.lo, y.lo) - min(x.hi, y.hi))
        far = max(abs(x.hi - y.lo), abs(y.hi - x.lo))
        lo2 += gap * gap
        hi2 += far * far
    return Iv(lo2 ** 0.5, hi2 ** 0.5)


# ── ВЕРШИНИ ─────────────────────────────────────────────────────────────────
class Item:
    """Річ у слоті. Атрибути — Iv, коди або None (невідомо). `pinned` — закріплена
    людиною (її річ або явний вибір); `own` — її власна річ (з фото)."""
    __slots__ = ("id", "slot", "a", "pinned", "own")

    def __init__(self, id, slot, pinned=False, own=False, **attrs):
        self.id, self.slot, self.pinned, self.own = id, slot, pinned, own
        self.a = attrs

    def get(self, k):
        return self.a.get(k)

    def __repr__(self):
        return "%s@%s" % (self.id, self.slot)


# ── ШАБЛОН ПРАВИЛА ──────────────────────────────────────────────────────────
class Template:
    """Шаблон гіперребра. Екземпляр = шаблон + прив'язка ролей до речей.

    scope:   "item" | "pair" | "set" | "slots" — як генеруються прив'язки;
    roles:   імена ролей (для "pair" — дві, для "set" — одна множинна);
    accepts: (hg, item) -> bool — чи може річ стати учасником;
    reads:   поля особи/нагоди, які шаблон читає (для інвалідації й кешу);
    applies: (hg, bind) -> (status, params, reason); status ∈ {"yes","no","unknown"};
    measure: (hg, bind, params) -> (Iv | None, missing[list], detail{dict});
    band:    (hg, params) -> (direction, lo, hi, unit) — напрям "le": добре, якщо
             вимір ≤ порогу; "ge": добре, якщо ≥; смуга [lo, hi] — власна
             невизначеність порогу в базі знань (T3 тощо), не наш допуск;
    polarity: "constraint" | "support";
    handles: ролі, які можна міняти при ремонті (None — усі не закріплені);
    tier/kb: рівень доказовості й якір у базі знань (для пояснення, не для ваги)."""

    def __init__(self, id, cls, polarity, scope, measure, band, applies=None, accepts=None,
                 reads=(), roles=("x",), handles=None, tier="T3", kb="", scale=1.0,
                 slots=None, uses_visibility=True):
        assert cls in CLASSES and polarity in ("constraint", "support")
        self.id, self.cls, self.polarity, self.scope = id, cls, polarity, scope
        self.measure, self.band = measure, band
        self.applies = applies or (lambda hg, bind: ("yes", {}, ""))
        self.accepts = accepts or (lambda hg, it: True)
        self.reads, self.roles, self.handles = tuple(reads), tuple(roles), handles
        self.tier, self.kb, self.scale = tier, kb, float(scale)
        self.slots, self.uses_visibility = slots, uses_visibility


class Factor:
    """Екземпляр гіперребра з вердиктом.

    Ідентичність: для item/pair — (шаблон, відсортовані id учасників); для множинних
    (set/slots) — (шаблон, "*"): ребро над усім образом одне, і заміна сторонньої
    речі не робить його «іншим» (інакше позиція стилістки над ним сиротіла б від
    заміни сережки). Хто саме в ролі винуватця — у `detail["culprits"]`."""
    __slots__ = ("tid", "bind", "verdict", "value", "band", "margin", "missing", "detail", "reason", "star")

    def __init__(self, tid, bind, star=False):
        self.tid, self.bind, self.star = tid, bind, star
        self.verdict = self.value = self.band = self.margin = None
        self.missing, self.detail, self.reason = [], {}, ""

    @property
    def key(self):
        return (self.tid, ("*",)) if self.star else (self.tid, tuple(sorted(i.id for i in self.bind)))


def classify(polarity, direction, value, lo, hi):
    """Інтервальне порівняння виміру зі смугою порогу → (вердикт, запас).

    Звук (soundness): OK/VIOLATE (SUPPORT/ABSENT) видаються, лише коли висновок
    однаковий для ВСІХ допустимих значень виміру й порогу; інакше BORDER. Запас —
    у рідних одиницях правила, додатний = «на добрій стороні»."""
    if direction == "le":                    # добре, якщо value ≤ поріг
        good, bad = value.hi <= lo, value.lo > hi
        margin = (lo - value.hi) if good else (-(value.lo - hi) if bad else 0.0)
    else:                                     # "ge": добре, якщо value ≥ поріг
        good, bad = value.lo >= hi, value.hi < lo
        margin = (value.lo - hi) if good else (-(lo - value.hi) if bad else 0.0)
    if polarity == "constraint":
        return (OK if good else VIOLATE if bad else BORDER), margin
    return (SUPPORT if good else ABSENT if bad else BORDER), margin


# ── ГІПЕРГРАФ ОБРАЗУ ────────────────────────────────────────────────────────
class HG:
    """Гіперграф одного образу в одному контексті.

    items: {слот: Item}; person, ctx: словники полів (Iv/коди/None).
    F: ключ → Factor; by_item: id речі → ключі; by_field: поле → ключі.
    Лічильник `evals` рахує обчислення шаблонів (для заміру інкрементальності)."""

    def __init__(self, templates, person, ctx, items):
        self.T = {t.id: t for t in templates}
        self.person, self.ctx = dict(person), dict(ctx)
        self.items = {it.slot: it for it in items}
        self.F, self.by_item, self.by_field = {}, {}, {}
        self.stances = {}
        self.evals = 0
        self.build()

    # ── похідна вершина: видимість (шари) ──
    def visible(self):
        """Речі, видимі в образі. Застебнутий верхній шар ховає верх (і сукню
        вище талії — тут спрощено до слота «верх»). Це ПОХІДНА вершина: від неї
        залежать прив'язки всіх шаблонів з `uses_visibility`."""
        out = self.items.get("верхній_шар")
        hidden = set()
        if out is not None and out.get("closed") is True:
            hidden.add("верх")
        return [it for s, it in sorted(self.items.items()) if s not in hidden]

    # ── прив'язки ──
    def _pool_for(self, t):
        src = self.visible() if t.uses_visibility else [it for _, it in sorted(self.items.items())]
        if t.slots is not None:
            src = [it for it in src if it.slot in t.slots]
        return [it for it in src if t.accepts(self, it)]

    def bindings(self, t, only_with=None):
        """Прив'язки шаблону. `only_with` — множина id: лише прив'язки, що містять
        хоч одну з цих речей (інкрементальне перебудування)."""
        xs = self._pool_for(t)
        if t.scope in ("item",):
            out = [(x,) for x in xs]
        elif t.scope == "pair":
            out = list(itertools.combinations(xs, 2))
        else:                                   # "set" / "slots": одна прив'язка на образ
            out = [tuple(xs)] if xs else []
        if only_with is not None and t.scope in ("item", "pair"):
            out = [b for b in out if any(x.id in only_with for x in b)]
        return out

    # ── оцінка одного екземпляра ──
    def evaluate(self, t, bind):
        self.evals += 1
        f = Factor(t.id, bind, star=t.scope in ("set", "slots"))
        status, params, why = t.applies(self, bind)
        if status == "no":
            f.verdict, f.reason = NA, why
            return f
        if status == "unknown":
            f.verdict, f.reason, f.missing = UNKNOWN, why, list(params.get("missing", []))
            return f
        value, missing, detail = t.measure(self, bind, params)
        f.detail = detail or {}
        f.missing = list(missing)
        if value is None:
            f.verdict = UNKNOWN
            return f
        direction, lo, hi, unit = t.band(self, params)
        f.value, f.band = value, (direction, lo, hi, unit)
        f.verdict, f.margin = classify(t.polarity, direction, value, lo, hi)
        if missing:
            # Відсутній вхід підставлено ВСІЄЮ областю значень. Якщо висновок однаковий
            # для всієї області — він рішучий і питати не треба («decided_despite»);
            # інакше це «без входу», а не «на межі» (K-IO-04: без входу ≠ пройдено).
            if f.verdict == BORDER:
                f.verdict, f.reason = UNKNOWN, "depends_on_missing"
            else:
                f.detail["decided_despite_missing"] = list(missing)
                f.missing = []
        elif f.verdict == BORDER:
            # BORDER розкладається на причину: вимір широкий чи поріг розмитий
            f.reason = "input_spread" if value.width() > 0 else "threshold_band"
        return f

    def _index(self, f):
        k = f.key
        self.F[k] = f
        for x in f.bind:
            self.by_item.setdefault(x.id, set()).add(k)
        for fld in self.T[f.tid].reads:
            self.by_field.setdefault(fld, set()).add(k)

    def _drop(self, k):
        f = self.F.pop(k, None)
        if f is None:
            return
        for x in f.bind:
            self.by_item.get(x.id, set()).discard(k)
        for fld in self.T[f.tid].reads:
            self.by_field.get(fld, set()).discard(k)

    def build(self):
        self.F, self.by_item, self.by_field = {}, {}, {}
        for t in self.T.values():
            for b in self.bindings(t):
                self._index(self.evaluate(t, b))

    def snapshot(self):
        return {k: f.verdict for k, f in self.F.items()}

    # ── заміна речі з інвалідацією залежних висновків ──
    def replace(self, slot, new):
        """Замінити річ у слоті (new=None — прибрати). Перебудовуються ЛИШЕ екземпляри,
        що (а) містять стару чи нову річ, (б) є множинними (set/slots), або (в) залежать
        від видимості, якщо заміна змінила видимість. Повертає дельту вердиктів."""
        before = self.snapshot()
        old = self.items.get(slot)
        vis0 = {x.id for x in self.visible()}
        if new is None:
            self.items.pop(slot, None)
        else:
            self.items[slot] = new
        vis1 = {x.id for x in self.visible()}
        dirty = (vis0 ^ vis1) | ({old.id} if old else set()) | ({new.id} if new else set())
        # 1) викинути все, що торкається брудних речей, і всі множинні екземпляри
        drop = set()
        for i in dirty:
            drop |= self.by_item.get(i, set())
        for k in list(self.F):
            if self.T[k[0]].scope in ("set", "slots"):
                drop.add(k)
        for k in drop:
            self._drop(k)
        # 2) перебудувати лише потрібне
        for t in self.T.values():
            if t.scope in ("set", "slots"):
                bs = self.bindings(t)
            else:
                bs = self.bindings(t, only_with=dirty)
            for b in bs:
                f = self.evaluate(t, b)
                if f.key not in self.F:
                    self._index(f)
        after = self.snapshot()
        return diff(before, after)

    def set_ctx(self, field, value, person=False):
        """Змінити поле нагоди (чи особи): перераховуються лише екземпляри шаблонів,
        що це поле ЧИТАЮТЬ (оголошене `reads`). Повертає дельту."""
        before = self.snapshot()
        (self.person if person else self.ctx)[field] = value
        for k in list(self.by_field.get(field, set())):
            f = self.F.get(k)
            if f is None:
                continue
            self._drop(k)
            self._index(self.evaluate(self.T[f.tid], f.bind))
        return diff(before, self.snapshot())

    # ── шар інтерпретації й вибору ──
    def declare(self, kind, tid, ids, reason, by):
        """Позиція над екземпляром: DELIBERATE_BREAK (стилістка) або PERSON_CHOICE
        (людина). Позиція НЕ міняє виміру; вона міняє дію (ремонт/умова/мовчання).

        Правила перевірки (записка §4.4):
          * екземпляр мусить існувати й бути VIOLATE/BORDER — інакше VOID;
          * DELIBERATE_BREAK не легітимізує PERSONAL/PHYSICAL — лише людина може
            обрати фізичний ризик своїм словом → REJECTED;
          * PERSON_CHOICE приймається, коли в екземплярі є закріплена річ або
            людина прямо попросила (by == "person")."""
        star = self.T[tid].scope in ("set", "slots")
        key = (tid, ("*",)) if star else (tid, tuple(sorted(ids)))
        f = self.F.get(key)
        st = dict(kind=kind, key=key, ids=tuple(sorted(ids)), reason=reason, by=by)
        cul = set((f.detail or {}).get("culprits") or ()) if f is not None else set()
        if f is None:
            st["status"] = STANCE_VOID
        elif star and cul and not set(ids) <= cul:
            st["status"] = STANCE_VOID          # позиція про речі, які не є винуватцями
        elif f.verdict not in (VIOLATE, BORDER):
            st["status"] = STANCE_VOID
        elif kind == DELIBERATE_BREAK and self.T[tid].cls in ("PERSONAL", "PHYSICAL"):
            st["status"] = STANCE_REJECTED
        elif kind == PERSON_CHOICE and not (by == "person" or any(x.pinned for x in f.bind)):
            st["status"] = STANCE_REJECTED
        else:
            st["status"] = STANCE_OK
        self.stances[key] = st
        return st

    def revalidate_stances(self):
        """Після замін: позиція над екземпляром, якого вже нема, — ORPHANED; над
        екземпляром, що став OK/NA, — VOID (розривати вже нічого)."""
        for key, st in self.stances.items():
            f = self.F.get(key)
            if st["status"] != STANCE_OK:
                continue
            cul = set((f.detail or {}).get("culprits") or ()) if f is not None else set()
            if f is None or (key[1] == ("*",) and cul and not set(st["ids"]) <= cul):
                st["status"] = STANCE_ORPHANED      # учасників, про яких була позиція, нема
            elif f.verdict not in (VIOLATE, BORDER):
                st["status"] = STANCE_VOID          # ламати вже нічого
        return self.stances

    # ── зведення без суми ──
    def profile(self):
        """Профіль образу: лічба вердиктів за класами. Жодного скаляра «краси»."""
        p = {c: dict(VIOLATE=0, BORDER=0, UNKNOWN=0, OK=0, SUPPORT=0, ABSENT=0, NA=0) for c in CLASSES}
        for k, f in self.F.items():
            st = self.stances.get(k)
            v = f.verdict
            if v == VIOLATE and st and st["status"] == STANCE_OK:
                v = "OK"   # у профілі дії — прийнята позиція знімає вимогу ремонту, не вимір
            p[self.T[f.tid].cls][v] += 1
        return p

    def vector(self):
        """Вектор для Парето: VIOLATE за класами, далі BORDER і UNKNOWN разом.

        SUPPORT у домінування НЕ входить: «когерентні пари не преміюються —
        це тягне до медіани» (тема-13 K-REG-05). Перша версія прототипу мала
        −SUPPORT у векторі, і фронт прикладу 3 звівся до одного «все коричневе»
        варіанта — рівно та пастка. Підтримки звітуються як здобуті/втрачені."""
        p = self.profile()
        return tuple(p[c]["VIOLATE"] for c in CLASSES) + (
            sum(p[c]["BORDER"] for c in CLASSES), sum(p[c]["UNKNOWN"] for c in CLASSES))

    def supports(self):
        return {k for k, f in self.F.items() if f.verdict == SUPPORT}

    # ── пояснення (структуровані заяви, не проза) ──
    def explain(self):
        out = dict(supports=[], tensions=[], borders=[], unknowns=[], stances=[], coverage={})
        cov = {}
        for k, f in sorted(self.F.items()):
            t = self.T[f.tid]
            c = cov.setdefault(t.cls, dict(instances=0, decided=0, unknown=0, na=0))
            c["instances"] += 1
            c["decided"] += f.verdict in (OK, VIOLATE, SUPPORT, ABSENT)
            c["unknown"] += f.verdict == UNKNOWN
            c["na"] += f.verdict == NA
            rec = dict(rule=f.tid, cls=t.cls, tier=t.tier, kb=t.kb,
                       roles={r: x.id for r, x in zip(t.roles, f.bind)} if t.scope in ("item", "pair")
                       else {t.roles[0]: list((f.detail or {}).get("culprits") or [x.id for x in f.bind])},
                       value=repr(f.value) if f.value is not None else None,
                       band=f.band, margin=None if f.margin is None else round(f.margin, 2),
                       detail=f.detail)
            st = self.stances.get(k)
            if st:
                rec["stance"] = dict(kind=st["kind"], status=st["status"], reason=st["reason"])
            if f.verdict == SUPPORT:
                out["supports"].append(rec)
            elif f.verdict == VIOLATE:
                hs = [x.id for x in handles(f)]
                rec["repair_handles"] = hs
                out["tensions"].append(rec)
            elif f.verdict == BORDER:
                rec["why"] = f.reason
                out["borders"].append(rec)
            elif f.verdict == UNKNOWN:
                rec["missing"] = f.missing or [f.reason]
                out["unknowns"].append(rec)
        out["stances"] = [dict(kind=s["kind"], key=s["key"], status=s["status"], reason=s["reason"])
                          for s in self.stances.values()]
        out["coverage"] = cov
        return out


def handles(f):
    """Ручки ремонту екземпляра: винуватці з виміру (роль у множинному ребрі —
    напр. «сирота»-метал, фокуси понад ліміт), інакше всі учасники; закріплені — ніколи."""
    cul = set((f.detail or {}).get("culprits") or ())
    xs = [x for x in f.bind if (not cul or x.id in cul)]
    return [x for x in xs if not x.pinned]


def diff(before, after):
    """Дельта вердиктів між двома знімками: додані, зниклі, змінені ключі."""
    added = {k: after[k] for k in after if k not in before}
    removed = {k: before[k] for k in before if k not in after}
    changed = {k: (before[k], after[k]) for k in after if k in before and before[k] != after[k]}
    return dict(added=added, removed=removed, changed=changed)


# ── РЕМОНТ: ЛОКАЛЬНИЙ ПОШУК У ОБЛАСТІ ГІПЕРРЕБРА ───────────────────────────

_TARGET_RANK = {OK: 0, SUPPORT: 0, NA: 0, "DISSOLVED": 0, BORDER: 1, UNKNOWN: 2, VIOLATE: 3, ABSENT: 3}


def _mapper(hg, src, old_id, new_id):
    """Функція «той самий екземпляр у знімку `src`» з підміною old→new у прив'язці.
    Множинний шаблон (set/slots) має один екземпляр на образ — шукається за шаблоном."""
    by_tid = {}
    for k in src:
        if hg.T[k[0]].scope in ("set", "slots"):
            by_tid[k[0]] = k

    def get(k):
        if k in src:
            return src[k]
        tid, ids = k
        if hg.T[tid].scope in ("set", "slots"):
            kk = by_tid.get(tid)
            return src.get(kk) if kk else None
        return src.get((tid, tuple(sorted((new_id if i == old_id else i) for i in ids))))
    return get


def repair(hg, key, pool, top=5):
    """Кандидати заміни ОДНІЄЇ речі в області гіперребра `key`.

    Ручки — учасники без `pinned`. Для кожного кандидата пулу: пробна заміна
    (інкрементальна), лексикографічний ранг без ваг:
      (стан цілі, нові VIOLATE за класами, втрачені SUPPORT, нові UNKNOWN),
    потім відкат. «DISSOLVED» — ціль зникла, бо нова річ не відповідає умові
    застосування шаблону (напр. нейтраль замість хроми): це не «виправлено», а
    «передумова знята», і так і позначено. Повертає топ і лічбу оцінок шаблонів."""
    f = hg.F[key]
    before = hg.snapshot()
    res, tried = [], 0
    ev0 = hg.evals
    for x in handles(f):
        for y in pool.get(x.slot, ()):
            if y.id == x.id or any(y.id == it.id for it in hg.items.values()):
                continue
            tried += 1
            hg.replace(x.slot, y)
            after = hg.snapshot()
            prior = _mapper(hg, before, y.id, x.id)     # ключ «після» → вердикт «до»
            later = _mapper(hg, after, x.id, y.id)      # ключ «до» → вердикт «після»
            tgt = later(key) or "DISSOLVED"
            k2 = key if key in hg.F else (key[0], tuple(sorted((y.id if i == x.id else i) for i in key[1])))
            tdet = dict(hg.F[k2].detail) if k2 in hg.F else {}
            new_v = [0] * len(CLASSES)
            new_u = lost_s = 0
            for k, v in after.items():
                was = prior(k)
                if v == VIOLATE and was != VIOLATE:
                    new_v[CLASSES.index(hg.T[k[0]].cls)] += 1
                if v == UNKNOWN and was != UNKNOWN:
                    new_u += 1
            gained = []
            for k, v in before.items():
                if v == SUPPORT and later(k) != SUPPORT:
                    lost_s += 1
            for k, v in after.items():
                if v == SUPPORT and prior(k) != SUPPORT:
                    gained.append(k[0])
            rank = (_TARGET_RANK.get(tgt, 4),) + tuple(new_v) + (lost_s, new_u)
            res.append(dict(slot=x.slot, out=x.id, inn=y.id, target_after=tgt, rank=rank,
                            new_violations={c: n for c, n in zip(CLASSES, new_v) if n},
                            lost_supports=lost_s, new_unknowns=new_u, gained_supports=gained,
                            target_detail=tdet))
            hg.replace(x.slot, x)
    res.sort(key=lambda r: (r["rank"], r["inn"]))
    return dict(candidates=res[:top], tried=tried, evals=hg.evals - ev0)


def pareto(variants):
    """Недоміновані варіанти за вектором (менше — краще в кожній компоненті)."""
    out = []
    for i, (vi, a) in enumerate(variants):
        dom = False
        for j, (vj, b) in enumerate(variants):
            if j != i and all(p <= q for p, q in zip(vj, vi)) and any(p < q for p, q in zip(vj, vi)):
                dom = True
                break
        if not dom:
            out.append((vi, a))
    seen, uniq = set(), []
    for v, a in out:
        if v not in seen:
            seen.add(v)
            uniq.append((v, a))
    return uniq


def tradeoffs(hg, slots, pool, cap=4):
    """Варіанти компромісу: усі заміни 0–2 речей у названих слотах (без закріплених),
    Парето-фронт за `HG.vector()`. Без суми й без «найкращого» — вибір за стилісткою
    та людиною; кожен варіант несе свій вектор, тож видно, що виграно й що віддано."""
    base = {s: hg.items.get(s) for s in slots}
    free = [s for s in slots if base[s] is not None and not base[s].pinned]
    variants = [(hg.vector(), {})]
    ev0 = hg.evals
    for r in (1, 2):
        for combo in itertools.combinations(free, r):
            choices = [[y for y in pool.get(s, ()) if y.id != base[s].id] for s in combo]
            for ys in itertools.product(*choices):
                for s, y in zip(combo, ys):
                    hg.replace(s, y)
                variants.append((hg.vector(), {s: y.id for s, y in zip(combo, ys)}))
                for s in combo:
                    hg.replace(s, base[s])
    front = pareto(variants)
    front.sort(key=lambda va: va[0])
    return dict(front=front[:cap], front_size=len(front), variants=len(variants), evals=hg.evals - ev0)
