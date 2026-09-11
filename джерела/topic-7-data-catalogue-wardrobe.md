# Topic 7 — Data, Catalogue, Wardrobe

**Single authoritative file. Replaces all previous topic-7 notes and audits.**

This file governs three parts of the system: the feed parser (`feed.py`), the attribute
extraction plan (`extract.py`), and the wear-probability priors behind the purchase gate and
the cost-per-wear denominator. Everything below was traced to the source that first stated it
and checked against that source's own text. Where a claim could not be verified, it says so at
the point of use rather than in a footnote.

**Self-containment standard.** Each block states mechanism, threshold and condition. If you have
to open the source to apply a rule, that block has failed and is marked as failed.

**Force ladder.** `hard` › `strong` › `default` › `soft` › `hint`. A rule's force may not exceed
its verification. An uncalibrated threshold is `hint` and carries the label *folkloric constant*.

**Provenance tags on every number.** `[spec]` normative platform documentation · `[measured]`
published empirical measurement · `[convention]` practitioner agreement without measurement ·
`[folkloric]` invented number, never calibrated · `[inferred]` our argument, not the source's
finding.

---

# PART 1 — FEED INGESTION

## 1.1 ROZETKA — XML requirements

Source: `sellerhelp.rozetka.com.ua/p185-pricelist-requirements.html`, revised 2026-06-29;
`/p188-product-grouping.html` and `/p205-product-variety.html`, revised 2026-06-12;
`/p210-product-characteristics.html`, revised 2026-06-12; `/p206-color-palette.html`;
`/st/ua/add-sizing-grid`.

### Element inventory (complete) `[spec]`

```
yml_catalog[date]
└ shop
  ├ name              shop name, no legal form
  ├ company           legal entity name
  ├ url               shop URL
  ├ currencies › currency[id, rate]        UAH USD EUR
  ├ categories › category[id, rz_id]       rz_id = ROZETKA's own category id
  └ offers › offer[id, available]
      ├ price, price_old|old_price, price_promo|promo_price, currencyId, categoryId
      ├ stock_quantity | quantity_in_stock          ← authoritative availability
      ├ url                                          product page on seller's site
      ├ picture                                      1..15, first = main
      ├ vendor                                       brand — required for grouping
      ├ article                                      seller's article/SKU code
      ├ name | model                                 ≤ 255 chars
      ├ name_ua | model_ua
      ├ description, description_ua                  ≤ 50 000 chars, HTML in CDATA
      ├ state                                        new | stock | used | refurbished
      ├ docket, docket_ua                            short description
      └ param[name, paramid, valueid]
          └ value[lang="uk"|"ru"]                    ← text characteristics only
```

**There is no `group_id` in this specification.** Not as an attribute, not as an element.

### Hard constraints `[spec]`

| Constraint | Value |
|---|---|
| Encoding | UTF-8 only |
| `offer id` | Latin letters and digits; no Cyrillic, no spaces; **frozen after publication** — changing it creates a duplicate product |
| `name` | ≤ 255 characters |
| `description` | ≤ 50 000 characters, HTML wrapped in CDATA |
| `param` value | ≤ 500 characters |
| `picture` URL | ≤ 1999 characters; direct link; Google Drive / cloud-share links rejected |
| `picture` count | 1..15 per offer |
| Characteristics | **minimum 3 per product** |
| Reserved XML chars | `&` `<` `>` `"` `'` must be escaped as entities |

### Variants and grouping — the decisive mechanism `[spec]`

Three separate pages state the same model, and it is the opposite of what a feed-native
`group_id` would imply:

1. **Every variant is its own offer.** Colour, size, volume, configuration — each is submitted
   as a separate unique position with its own id, price, images, description and
   characteristics.
2. **Grouping happens marketplace-side, during moderation**, not in the file. Variants are
   joined when the item is admitted to the marketplace and then displayed with a variant
   selector.
3. **Grouping is per-category and rule-driven.** For variants to group, each position must
   carry (a) the characteristic that the category groups on, (b) a brand (`vendor`), and (c) a
   distinguishing mark inside the product name. Grouping occurs only within a single category.
   Some categories group on more than one parameter at once — colour *and* size. Reduced, used
   and refurbished items are excluded from grouping.

**The grouping characteristic for our vertical is named explicitly: for clothing and footwear
categories, it is SIZE** `[spec]`. This is not an inference. It means a dress in 3 colours × 5
sizes is 15 offers in the file, and the file contains no key that says which 15 belong together.

**Consequence for the parser:** the grouping key must be *reconstructed*. Available material,
in descending reliability: `article` (many ERP exporters put model identity here precisely
because nothing else exists) → `vendor` + `categoryId` + name-stem → nothing.

### Characteristic types and serialization `[spec]`

Ten types. The serialization differs per type and this is where silent data loss happens.

| Type | Meaning | Feed form |
|---|---|---|
| `List` | several values from a list | **comma-separated** |
| `List Values` | multi-select from a list | multi |
| `ComboBox` | single choice | exactly one value |
| `Checkbox` | boolean | `так`/`ні` or `є`/`немає` |
| `CheckBoxGroup` | multi-select from a set | **comma-separated** |
| `CheckBoxGroupValues` | multi-select from a set | multi |
| `Integer` | whole number | number |
| `Decimal` | fractional number | number |
| `TexInput` | short free text | may carry `<value lang>` children |
| `TextArea` | long free text | may carry `<value lang>` children; **`<br/>` is the visual separator between multiple values** |

- `valueid` is **mandatory** whenever `paramid` is supplied, for every type except
  `TexInput`/`TextArea`. It may itself be a comma-separated list matching a comma-separated
  value list. The specification's own example is a season parameter carrying three ids and
  three values.
- Characteristic **names** must be filled in **one language only**. Value bilinguality goes
  through `<value lang="uk">` / `<value lang="ru">`, never through the name.
- **Cross-category parameters** («наскрізні») exist and apply across categories: warranty,
  country of manufacture, country of brand registration.
- The exported reference carries a **filter-type column**: `main` = the parameter drives
  category faceting on site; `disable` = it does not. This tells you which attributes the
  marketplace itself considers discriminating.

### Open-world vocabulary — verified normatively `[spec]`

A characteristic value that does not yet exist in the category — **a new colour or a new size**
— is **added automatically to the reference when the products are admitted**. If a needed value
is absent, the seller supplies it and it enters the reference during moderation. Creating a new
*characteristic* (as opposed to a new value) is a slow manual process taking months.

**This is decisive for the colour layer.** The reference against which colour names are matched
absorbs every new name a seller invents. A reference that admits all new values is not a
controlled vocabulary — it is a log of what sellers have written. There is no closed colour
list to validate against.

### What `p206-color-palette` actually is `[spec]`

It is **not** a colour dictionary. It governs goods sold by named shade (its own example is hair
dye) and requires the seller to supply **photographs of shade swatches**, with the shade string
matching across three places: the product name, the colour characteristic, and the swatch image
filename. It defines no colour list and cannot serve as colour ground truth.

### Size tables are not in the feed `[spec]`

The brand measurement table behind the «Таблиця розмірів» button on a product page is produced
by downloading a spreadsheet template, filling the tab for the relevant category, and **sending
it to support as a ticket attachment**. It is not a feed element, not a param, and has no
machine-readable endpoint. Any brand measurement table must be scraped from the product page or
the shop's own site — a different ingest path with a different failure mode from YML parsing.

### K-SIZ-02 — a nominal size does not predict fit `[new, verification run 3, 2026-09-06]`

> **ID note.** The patch file names this rule `K-SIZ-BRAND-01`. That form is **not readable by
> the corpus registry**: every ID in the 379-code corpus is `PREFIX-3…5-NN`, and both readers
> (`gate_reach.з_корпусу`, `audit_contracts._корпус`) match exactly that shape. A four-part ID
> is invisible to them — it can never be counted, never traced, never flagged as outside the
> corpus. A rule the gates cannot see is the *silence ≠ passed* failure by construction, so the
> rule is registered as **K-SIZ-02**, not `K-SIZ-01`: that number is already taken by
> тема-10 ("Кожен аксесуар кріпиться до виміру тіла"). This is worth stating plainly, because
> С0 step 3 prescribes the mapping `K-SIZ → тема-7` — and the K-SIZ family was **already**
> claimed by тема-10 before that step was written. The prefix is therefore shared across two
> themes: `K-SIZ-01` accessory-to-body sizing (тема-10), `K-SIZ-02` nominal size vs fit
> (тема-7). Any future code mapping a whole prefix to one theme will be wrong for one of them.

**Source.** "The economics of vanity sizing", *J. Economic Behavior & Organization* 2017 `[abs]`
(54 US retailers): in menswear and childrenswear vanity sizing is almost absent; in womenswear
the nominal label is inflated at brands in the moderately higher price segment, while designer
brands run smaller. Esquire (A. Sauer, 2010) `[⚠]`: for a nominal 36″ waist the real garment
measures 37–41″ (94–104 cm) — a spread of ≈10 cm between brands. UK 2011 `[⚠]`: waist
understated by 3.8–5.1 cm; "medium" varies by up to ≈12 cm in the bust between brands.
Standards named but not opened: ISO 8559-1/-2, EN 13402, ASTM D5585/D6240; ДСТУ — not opened.

**FORCE:** `strong` for the mechanism (T1 — measured: nominal ≠ prediction); **`hint` for every
number** (`[⚠]`, `[folkloric constant]` until measured on Ukrainian brands).
**WHEN:** a nominal size is used as an input to fit, and garment measurements in centimetres are
absent.
**BREAKS:** when garment measurements in cm are present (then `fit.тіло` works directly);
childrenswear.
**CHANGES:** *before* — a size from the feed could become a fact about fit. *after* — a nominal
size without garment measurements is a **question**, never a "fits"; the explanation shows the
size as a range; a per-brand offset table in `магазини.tsv` is filled from fittings and returns,
not from research. This closes cell II.5 of the domain×corpus matrix at the level of the rule;
the code is a separate session.

**Relation to the section above.** This is the styling-side consequence of *Size tables are not
in the feed*: the platform gives a label and withholds the measurements behind it, so the label
is the only size input we have — and it is precisely the input that does not predict fit.

### What is behind a seller login and therefore unavailable to us

- The per-category dictionary of characteristics and permitted values («Довідники», under
  Управління товарами).
- The per-category grouping rules («Правила групування»).

Both are account-gated with no public endpoint. Everything above about *types and separators* is
public and verified; nothing about *which characteristic names apparel categories actually use*
is available without a seller account.

---

## 1.2 PROM — YML import format

Source: `support.prom.ua/hc/uk/articles/360004963538` (Імпорт через YML — формат файлу);
Prom «Робота з Rozetka» app documentation.

### Offer attributes `[spec]`

```
<offer id="…" available="…" in_stock="…" type="vendor.model" selling_type="…" group_id="…">
```

| Attribute | Semantics |
|---|---|
| `id` | position id |
| `available` | **three states**: `склад` or `true` = in stock · **empty string = NOT in stock** · `false` = not in stock |
| `in_stock` | ready to ship |
| `type` | when `vendor.model`, the name is assembled from `typePrefix + vendor + model` and **`<name>` is ignored entirely** |
| `selling_type` | product type (retail / wholesale / both) |
| `group_id` | **numeric, 1–999999999**; marks the main product together with its variants; **the first offer in the list is the main one** |

### Elements `[spec]`

- `<name>` / `<name_ua>`, `<description>` / `<description_ua>`, `<keywords>` / `<keywords_ua>`.
  Dependency worth knowing: the Ukrainian name will not update without the Ukrainian
  description present, and vice versa.
- `<quantity_in_stock>` takes priority over `<stock_quantity>`.
- `<vendorCode>` takes priority over `<barcode>`, which takes priority over `<article>`.
- `<oldprice>` › `<price_old>` › `<old_price>` in priority order; discounts run 30 days.
- `<param name="…" unit="…">` — for multi-valued characteristics, **several values separated by
  `|`**.
- Limits: **up to 100 characteristics** and **up to 10 pictures** per offer; feed ≤ 180 MB.
- Dimensions block: weight in kg, width / height / length in cm.
- Regions: max 3; variants inherit the main product's region.
- `gtin`, `mpn` for Google Merchant compatibility.
- Categories: `category[id, parentId, portal_id, portal_url]`.
- Currencies: UAH, USD, EUR, BYR, KZT.

### The Prom → Rozetka bridge `[spec]`

The Prom app that generates a ROZETKA price list writes **`<group_id>` as a child element**, not
as an attribute — and the resulting varieties still require manual moderation on the ROZETKA
side before they display.

**So `group_id` occupies three different syntactic positions across the platforms we ingest:
an attribute (Prom native), a child element (Prom→Rozetka export), and nowhere at all
(Rozetka native).**

---

## 1.3 GOOGLE MERCHANT CENTER — product data specification

Source: Google Merchant Center product data specification; attribute pages for `item_group_id`,
`size`, `color`, `availability`. This is the international reference the UA platforms partially
imitate, and it states the variant model more sharply than either of them.

### Variants `[spec]`

- Variants are products differing only in details such as colour and size. `item_group_id`
  groups a product and its variants so they display as a group rather than separately.
- **Canonical apparel example: a product in 2 colours × 3 sizes is submitted as 6 variants**,
  all sharing one `item_group_id`.
- A product carrying `item_group_id` **must have at least one detailed product attribute** —
  Google looks for the varying attribute automatically.
- `item_group_id` must be unique per group and stable over time.

### Size `[spec]`

- **Required** for Shopping ads in *Apparel & Accessories › Clothing* (category 1604) and
  *› Shoes* (187).
- Each size is a separate product with the same `item_group_id`.
- Multiple sizes for one item are joined with a **slash**, never a comma (`S/M`, not `S, M`).
- `size_type` (regular, petite, plus, tall, big, maternity) and `size_system` are separate
  attributes.

### Colour `[spec]`

- **Required** for *Apparel & Accessories* (166) and for all variants in a group that differ by
  colour.
- Carries the **dominant colour first**, then **up to two accent colours**, combined with `/`
  **in order of prominence**. So `Black/Green` is one product with two colours, not one colour
  name. Maximum three colours.
- Invalid values: `multicolor`, `various`, `variety`, `assorted`, `N/A`, and any value that is
  really a size or a gender (`mens`, `womens`). Concatenated colour words without separators
  (`RedPinkBlue`) are rejected.
- For **non-deformable** apparel goods — jewellery, wooden accessories — where finish or
  material is equivalent to colour, the finish or material name may be submitted in the colour
  attribute.
- `gender` and `age_group` are required for apparel alongside colour and size.

---

## 1.4 The cross-platform contradiction table

This is the table to code against. Every row is a place where a parser written for one platform
silently produces wrong output on another.

| Concern | Rozetka | Prom | Google Merchant |
|---|---|---|---|
| Variant grouping key | **absent** — reconstructed marketplace-side at moderation | `group_id` **attribute** on `<offer>`, numeric | `item_group_id` element |
| Same key, exported | `<group_id>` **child element** via Prom's Rozetka app | — | — |
| Grouping axis for apparel | **size** (per-category rule) | seller-defined | colour × size |
| Multi-value separator | **comma** | **`\|`** | **`/`** (colour, in prominence order) |
| Second text separator | `<br/>` inside text characteristics | — | — |
| Availability | `stock_quantity` / `quantity_in_stock`; absent ⇒ out of stock | `available`: `склад`/`true` in · **`""` out** · `false` out | `availability` enum |
| Bilinguality | `<value lang="uk"\|"ru">` inside `<param>`; names single-language | separate `name_ua` / `description_ua` elements | one locale per feed |
| Name construction | `name` \| `model` | `name`, **or** `typePrefix+vendor+model` when `type='vendor.model'` — then `name` ignored | `title` |
| Model/article identity | `article` | `vendorCode` › `barcode` › `article` | `mpn`, `gtin` |
| Picture limit | 15 | 10 | — |
| Characteristic floor | **min 3** | — | ≥ 1 detailed attribute if grouped |

## 1.5 What the specifications do **not** contain

Stated because their absence is what the corpus previously assumed away:

- **No garment measurements.** No bust/waist/hip/length in cm anywhere in any of the three
  specifications. Fit data is not ingestable from a feed.
- **No brand size table.** Manual spreadsheet, support ticket, Rozetka only.
- **No canonical colour list.** The reference is per-category, private, and self-extending.
- **No garment-part structure.** No collar type, no sleeve construction, no closure — these
  exist only as free-text characteristics if a seller chose to supply them.
- **No fabric composition field.** Only as a characteristic, unvalidated, free-text in practice.
- **No occasion, formality, or style tag** of any kind.

Everything the composer needs beyond category, colour, price, brand and images must come from
image extraction or from the shop's own site — never from the feed.

---

# PART 2 — WHAT THIS MEANS FOR `feed.py`

## 2.1 The current read

```python
id=o.get("id"), group_id=o.get("group_id"), available=o.get("available") != "false",
назва=(o.findtext("name") or "").strip(),
params = {(p.get("name") or "").strip().lower(): (p.text or "").strip() …}
колір_назва = params.get("колір") or params.get("цвет") or params.get("color")
```

```python
моделі = {c.get("group_id") or c["id"] for c in придатні}
```

## 2.2 Defect table

Ordered by effect on the number the retrieval layer is judged on.

| # | Defect | Mechanism | Consequence |
|---|---|---|---|
| **D1** | `group_id` read only as an `<offer>` attribute | Rozetka has no such field; Prom→Rozetka uses a child element | `None` on both; `покриття` silently falls back to `c["id"]` |
| **D2** | Model count collapses to SKU count | Rozetka mandates one offer per size, and size is the apparel grouping axis | A dress in 3 colours × 5 sizes reports **15 models** where the answer is 3. Inflation ≈ size-grid depth, typically 4–7 for apparel |
| **D3** | `available` is parsed and never used | — | Out-of-stock offers enter the catalogue and count toward coverage. Coverage measures what a shop once listed, not what can be bought |
| **D4** | `available != "false"` is the wrong test | Prom's empty `available=""` means out of stock | Empty-availability offers counted as available |
| **D5** | `stock_quantity` / `quantity_in_stock` never read | On Rozetka this is the authoritative field; absence ⇒ out of stock | Availability unknowable on the platform that matters most |
| **D6** | Param text taken as `p.text` | For `<param><value lang="uk">Чорний</value></param>`, `p.text` is the whitespace before the first child | Bilingual colour params read as **missing**, not as wrong |
| **D7** | Multi-value params treated as atoms; **three separators exist** | Rozetka comma, Prom `\|`, Google `/` | `Чорний, Білий` becomes one lexicon key. `Black/Green` becomes one colour name |
| **D8** | `<br/>` inside text characteristics | Outside CDATA it becomes a child element | Second, independent truncation path for `p.text` |
| **D9** | `name_ua` never read; `type='vendor.model'` unhandled | Name is assembled from other fields on such feeds | `назва` empty ⇒ `слот()` runs on category alone and `verify.перевірити(назва=…)` loses its witness; colour control degrades to "без контролю" without saying so |
| **D10** | No diagnostic on grouping-key resolution | — | D1 fails **silently**. Every coverage figure ever produced from a Rozetka feed is unverifiable |

## 2.3 The consequence that matters most: the lexicon's quality gate defeats itself

`лексикон()` groups measured Lab by colour name and gates on internal spread:

```python
розкид = statistics.median(de00(центр, l) for l in labs)
придатна = розкид < 10.0
```

The gate exists to separate a colour word from a marketing word. Under D1 + D2, the *k* size
variants of one design are *k* separate catalogue rows **sharing the same first picture URL**.
The same photograph is measured *k* times, so those *k* Lab values are identical. Every
duplicated design pushes median spread toward zero and pushes `n` up by *k*.

A name can therefore reach `n = 40, розкид = 1.2, придатна = True` from six designs
photographed once each. **The gate reports highest confidence exactly where the evidence is most
redundant.** A filter that passes by construction is not a filter.

This matters more than it first appears, because §1.1 established there is **no public canonical
colour vocabulary for Ukrainian retail**. The measured lexicon is not a convenience — it is the
only available route to one. The defect corrupts the single instrument that could produce what
nobody publishes.

**Before / after.** Before: «мокко» reads as a well-defined colour, n=40, spread 1.2, and enters
the working vocabulary. After: n=6 distinct designs, spread recomputed across designs, and
«мокко» either survives on real evidence or is flagged. The two answers differ on whether a name
enters the system's colour vocabulary.

## 2.4 Feed rules

- **R-FEED-01 `[hard]`** The variant grouping key is **platform-dependent and may be absent**.
  Resolve in order: `<offer group_id="…">` (Prom) → `<group_id>` child (Prom→Rozetka) →
  `article` / `vendorCode` (Rozetka family) → reconstruct `vendor + categoryId + name-stem` →
  none. *Applies:* every YML ingest. *Breaks:* when a shop populates `article` per-size rather
  than per-model — detectable, because then `|article| == |offer|` within a category.
- **R-FEED-02 `[hard]`** `прогін` must report **`ключ_моделі_покриття`** — the fraction of
  offers with a resolved grouping key, broken down by branch — alongside `моделей`. Below ~0.5,
  `моделей` is not a model count and must be labelled as such in the report. *Rationale:* D1 and
  D10 fail silently; without this number no coverage figure is interpretable.
- **R-FEED-03 `[strong]`** Availability is a three-state read: `stock_quantity` /
  `quantity_in_stock` > 0 → in stock; else `available ∈ {true, склад}` → in stock; else out.
  **Empty string is out of stock.** Out-of-stock offers may remain in the catalogue but must be
  excluded from coverage counting.
- **R-FEED-04 `[strong]`** Param extraction reads `p.text` **or** the concatenation of
  `<value lang="uk">` / `<value lang="ru">` children, preferring `uk`; strips `<br/>`; then
  splits on **`,` (Rozetka), `|` (Prom), `/` (Google colour)**, keeping the first token as
  dominant and the rest as accents.
- **R-FEED-05 `[default]`** Name resolution order: `name_ua` → `name` →
  `typePrefix + vendor + model` when `type='vendor.model'`. The name is not a colour source but
  it is the cheapest witness `verify.py` has; losing it silently is worse than losing it loudly.
- **R-FEED-06 `[strong]`** The lexicon aggregates **per design, not per SKU**. Deduplicate on
  the resolved grouping key, and where no key resolves, deduplicate on picture URL. Report `n`
  as distinct designs. *Fail case prevented:* the self-defeating spread gate in §2.3.
- **R-FEED-08 `[default]`** When a feed carries **no colour param at all**, the colour word is
  taken **from the product name**, through the same `verify.назва_кольору` (word-boundary match,
  trap-list); a param, when present, keeps priority — it is more precise than a grid-truncated
  title. The resolved name enters as a lexicon **window** (zone, not point) with confidence 0.35,
  identical to the param branch. *Fail-case (2026-08-24, `stolyarchuk_com_ua.xml`, 24 SKUs):*
  the `назва_вікно` branch read only the param, so a feed whose every row names the colour in the
  title («Сукня 837.3 зелений»; 23/24 rows by the 08-23 measurement) returned `з_кольором = 0` —
  the live path was blind exactly where the word stood in plain sight. After the fix: 24/24
  resolve via `назва_вікно`; 8 of 18 dress windows non-empty; the justified pick carries
  `частка_вікна = 0.125`. *Where it breaks:* (1) grid-truncated names may simply omit the colour —
  that is an honest `None`, not a guess; (2) name-as-source makes the name-witness control
  tautological, already handled (`вердикт="джерело=назва"`); (3) lexicon window widths are T3, so
  every downstream number stays `hint`. Gate: `check_edits.py` §17 (ager_brief · stolyarchuk).

- **R-FEED-07 `[default]`** Fit and measurement data are **not ingestable from any UA feed**.
  Any module expecting garment measurements from the catalogue is mis-designed; the data must
  come from page scraping or from image extraction. *Fail case prevented:* building a fit-match
  layer on a field that does not exist.


---

# PART 3 — ATTRIBUTE EXTRACTION: THE FASHIONPEDIA ONTOLOGY

Source: Jia, M., Shi, M., Sirotenko, M., Cui, Y., Cardie, C., Hariharan, B., Adam, H.,
Belongie, S. *Fashionpedia: Ontology, Segmentation, and an Attribute Localization Dataset.*
ECCV 2020, pp. 316–332; arXiv:2004.12276. Cornell / Cornell Tech / Google Research / Hearst
Magazines. Full text verified against the ECCV open-access version.

## 3.1 Structure `[measured]`

- **46 apparel objects = 27 main apparel items + 19 apparel parts.**
- **294 fine-grained attributes across 9 super-categories.**
- Categories are held **separate** from attributes — a design decision, because a garment
  category is what an object *is* and an attribute is a property it *has*. Prior fashion
  datasets conflated them.
- Three relationship types: **meronymy** (outfit → garment → part), **garment/part → attribute**,
  and **hyponymy** to a **maximum of four levels**. The paper's own example: fleece ⊂ weft knit
  ⊂ knit fabric.
- Attributes are provided for **13 main outerwear categories** and **5 of the 19 parts**
  (sleeve, neckline, pocket, lapel, collar). Coverage is deliberately uneven — the other 14
  parts carry no attributes.

### The 27 main apparel items `[measured]`

Grouped as the ontology groups them:

- **Outerwear (13, attribute-bearing):** shirt/blouse, top/t-shirt/sweatshirt, sweater,
  cardigan, jacket, vest, pants, shorts, skirt, coat, dress, jumpsuit, cape
- **Accessories:** glasses, hat, headband/head covering/hair accessory, tie, glove, watch, belt,
  leg warmer, tights/stockings, sock, shoe, bag/wallet, scarf, umbrella

### The 19 apparel parts `[measured, 18 of 19 identified]`

collar · sleeve · neckline · lapel · pocket · epaulette · buckle · zipper · applique · bead ·
bow · flower · fringe · ribbon · rivet · ruffle · sequin · tassel

Grouped in the ontology as *garment main parts*, *bra parts*, *closures*, *decorations*. The
19th could not be read off the published figure; treat this list as 18 confirmed.

## 3.2 The 9 attribute super-categories `[measured]`

This is the vocabulary R-FP-03 requires. Values below are those readable in the published
ontology figure; the paper states 294 total, so treat these lists as substantially but not
exhaustively complete.

**1 · Silhouette** — asymmetrical, symmetrical, peplum, circle, flare, fit-and-flare, trumpet,
mermaid, balloon/bubble, bell, bell-bottom, bootcut, peg, pencil, straight, A-line,
tent/trapeze, baggy, wide-leg, high-low; and fit values: curved, tight/slim/skinny, regular,
loose, oversized

**2 · Waistline** — empire, dropped, high-waist, normal, basque, low-waist/low-rise,
no-waistline

**3 · Length (hemline)** — above-the-hip, micro, mini/mid-thigh, above-the-knee, knee/knee-high,
below-the-knee, midi/mid-calf/tea-length, maxi/ankle, floor/full

**4 · Sleeve length** — sleeveless, short, elbow-length, three-quarter, wrist-length

**5 · Opening type** — single-breasted, double-breasted, lace-up, wrap, zip-up, fly, chained,
buckled, toggled, no-opening

**6 · Non-textile material** — plastic, rubber, metal, straw, feather, gem/gemstone, bone,
ivory, fur/faux-fur, leather/faux-leather, suede, shearling, crocodile, snakeskin, wood, none

**7 · Textile finishing / manufacturing technique** — burnout, distressed/ripped, washed,
embossed, frayed, printed, ruched, quilted, pleated, gathered, smocking/shirring,
tiered/layered, cutout, slit, perforated, lined, applique/embroidery/patch, bead, rivet/stud/
spike, sequin, none

**8 · Textile pattern** — plain, abstract, cartoon, letters-and-numbers, camouflage,
check/plaid/tartan, dot, fair isle, floral, geometric, paisley, stripe, houndstooth,
herringbone, chevron, argyle, animal (leopard, cheetah, zebra, giraffe, snakeskin), peacock,
toile de Jouy, plant

**9 · Nickname** — garment-type-specific names (the paper's worked failure case is *welt*
pocket). This super-category is where the long tail lives and where a model most often supplies
a plausible-but-wrong term.

## 3.3 Dataset and annotation `[measured]`

- 50,527 images harvested from Flickr and free-licence photo sites; **48,825 retained** after
  filtering. Splits: 45,623 train / 1,158 validation / 2,044 test.
- Segmentation masks by **28 crowd workers** (10 days of training). Fine-grained attributes by
  **15 fashion experts** — graduate students in the apparel domain. Attributes were **never**
  crawled from retail descriptions.
- Annotators had two escape options: **"not sure"** and **"not on the list"**.
- **Fewer than 15% of masks per attribute super-class** were marked *not on the list* — an
  ontology-completeness result.
- *Not sure* concentrates in three super-classes: **Opening Type, Waistline, Length**. The
  paper states the cause directly: some masks show only a limited portion of the apparel — its
  example is **a top worn underneath a jacket** — so the expert cannot judge, on account of
  occlusion and viewpoint discrepancy.
- **Image composition:** on average **1 person, 3 main garments, 3 accessories and 12 garment
  parts per image.** Mean image dimensions **1710 × 2151**.
- Per image: **7.3 masks** (median 7, max 74), 5.4 categories, **16.7 attributes** (max 57).
  Per mask: **3.7 attributes** (max 14).
- Ontology built and verified by fashion experts, informed by four streams: leading e-commerce
  (ZARA, H&M, Gap, Uniqlo, Forever21); luxury houses (Prada, Chanel, Gucci); trend forecasting
  (WGSN); academic resources.
- Fashionpedia masks have the **highest boundary complexity of five compared fashion datasets**
  (≈8.36–8.39 mean vs 4.63 for DeepFashion2) — garments are geometrically harder to outline
  than the datasets that preceded it.

## 3.4 Model results — and exactly what they measure `[measured]`

Attribute-Mask R-CNN = Mask R-CNN plus a multi-label attribute head trained with sigmoid
cross-entropy. **It is not a vision-language model.**

| Metric, SpineNet-143 backbone | Value |
|---|---|
| Box AP (standard IoU) | **48.7** |
| Box AP with attribute-F1 added to the true-positive definition | **35.7** |
| Mask AP overall (IoU / IoU+F1) | 43.1 / 33.3 |
| Mask AP, **outerwear** | **64.1** / 40.7 |
| Mask AP, **accessories** | **56.1** |
| Mask AP, **garment parts** | **19.3** / 13.4 |
| AP large / medium / small | 50.0 / 40.2 / **17.3** |

Error decomposition: the Fashionpedia detector shows **no single dominant error type**
(localisation +13.4, classification +6.9, background +6.6), whereas a COCO-trained detector is
dominated by localisation (+28.3) and background (+15.7). Small objects collapse regardless —
AP 17.3 for small vs 50.0 for large.

## 3.5 The regime-transfer error `[inferred]`

The corpus converted the figures above into a rule of force `hard` describing "empirical VLM
reliability". Two independent problems with that conversion:

**(a) Wrong image regime.** Fashionpedia's images are daily-life, street-style, celebrity-event
and runway photographs of **dressed people** — 1 person, 3 garments, 3 accessories, 12 parts per
frame. The stated cause of the *not sure* concentration is **mutual occlusion between garments
on a body**.

Our extraction input is a **catalogue product photograph of one garment**, often flat-lay or
ghost-mannequin, on a clean background. `feed.py` already encodes that assumption: it crops the
centre 55% and discards near-white low-chroma pixels as background. **The occlusion regime that
generated Fashionpedia's finding does not exist in our input.** A waistline is unreadable when a
jacket covers it; it is not unreadable on a flat-lay of the dress alone.

The direction may still hold for other reasons — foreshortening on a model shot, a hem cropped
out of frame — but those are different mechanisms with different magnitudes, and none of them
were measured by this paper.

**(b) Wrong metric, wrong model class.** AP 19.3 for parts is a **mask-localisation** average
precision for small objects inside cluttered full-body photographs — consistent with the general
small-object collapse (AP 17.3). It measures whether a model finds and outlines a collar, not
whether a model can *name* a collar type on a 2000-pixel product shot of one shirt.

## 3.6 Extraction rules

| Rule | Content | Force |
|---|---|---|
| **R-FP-01** | Category and attribute are separate axes. A garment's category is what it *is*; attributes are what it *has*. Never fold one into the other in the schema. *Structural, regime-independent.* | `default` |
| **R-FP-02** | Attribute coverage is legitimately uneven. 13 of 27 main items and 5 of 19 parts carry attributes in the reference ontology; do not treat missing attribute slots as extraction failures. | `default` |
| **R-FP-03** | Use the 9 super-categories as the completeness checklist for our own attribute vocabulary. Anything our schema cannot express in these nine has a hole. *This is a checklist, not a measurement.* | `default` |
| **R-FP-04** | Reliability markers by attribute type (opening/waistline/length low; category/silhouette/pattern high). **Demoted from `hard`.** Evidence comes from worn-on-body imagery via a segmentation metric; unmeasured on catalogue photographs. Label: *borrowed regime*. | `hint` |
| **R-FP-05** | Hyponymy runs at most four levels deep. Our taxonomy should not exceed this without a reason — the reference ontology, built by domain experts across e-commerce, luxury and forecasting sources, did not need more. | `default` |
| **R-FP-06** | **Always provide an escape hatch.** Every extraction prompt must permit "not sure" and "not on the list" and must never force a label. Grounded on the `<15% not-on-list` figure, which is an **ontology-completeness** measure and therefore regime-independent — a vocabulary is incomplete or it is not, whatever the photograph looks like. | `hard` |
| **R-FP-07** | Nickname-class attributes are the highest-risk output: the reference model's own published failure is a wrong pocket nickname. Require a confidence signal on nickname outputs specifically, or drop the class. | `default` |
| **R-FP-08** | Maintain a crosswalk from our attribute names to Fashionpedia synsets, so external comparison remains possible. | `default` |

### Downstream correction

`R-ONT-05` justifies flattening garment parts out of the schema with two reasons: (а) parts AP
19.3, (б) the UA feed does not structure parts either. **Reason (а) is void** — 19.3 is a
segmentation AP on small objects in cluttered scenes. **Reason (б) survives intact and is
sufficient alone** (§1.5 confirms no part structure exists in any UA feed). The decision does
not reverse; its justification loses half its weight, which matters the next time someone asks
whether to add a parts layer.

### The measurement that would replace the borrowed number

60 SKUs from one verified Tier-A UA shop, stratified 20 flat-lay / 20 ghost / 20 model-front.
Extract the three super-categories the corpus marks low-reliability (opening type, waistline,
length) plus one it marks high (textile pattern). Single human adjudicator, binary correct /
incorrect. Predictions recorded in advance:

- **P1** On flat-lay and ghost shots, length and waistline agreement exceeds 85% — the borrowed
  "low reliability" label does not transfer. If agreement is below 85%, R-FP-04 is re-earned in
  our regime and returns to `strong`.
- **P2** Opening type separates from the other two, because closure visibility depends on
  whether the garment was photographed done up — a property of the shot, not of occlusion by a
  second garment. Expect the widest flat-lay/model-front gap of the three.
- **P3** Model-front shots trail flat-lay on all three by a margin larger than the
  pattern-recognition margin — the only part of the Fashionpedia finding that should survive
  transfer.

A result contradicting P1 is the useful one: it would mean the corpus reached a right conclusion
by an invalid route, and the route can be replaced without changing the rule.


---

# PART 4 — WARDROBE USE: BASE RATES AND PRIORS

## 4.1 The instruments

Four independent measurements, two methods, three countries. Knowing which is which matters,
because they disagree in specific places.

| Study | Method | n | Scope |
|---|---|---|---|
| **WRAP 2022** (UK) *Citizen Insights: Clothing Longevity and Circular Business Models Receptivity in the UK*; fielded Oct–Nov 2021 | Online panel **self-report**, quotas on age, gender, region | 6,000 adults who buy clothing for themselves at least annually; **44,807 items** discussed; separate 2,100-person CBM survey | **Includes** underwear, socks, hosiery |
| **Vermeyen et al. 2025** (Flanders) *Behind Closed Doors*, J. Circular Economy 3(1), CC-BY, doi 10.55845/OQEE5977 | **In-home physical audit**, researcher present, systematic count of every garment | 156 adults, 2024 | **Excludes** underwear, swimwear, accessories (gloves, scarves, hats, bags), shoes |
| **Vermeyen et al. 2026** (Flanders) *Unravelling the service lifespan of garments*, Cleaner and Responsible Consumption vol. 21 | Same audit method + structured interview | 160 adults; merged analyses use 156+160 | Same exclusions |
| **Dunne, Zhang & Terveen 2012** (US) *An Investigation of Contents and Use of the Home Wardrobe*, UbiComp '12 pp. 203–206, doi 10.1145/2370216.2370247 | Wardrobe contents + **daily dressing diaries** | **11 wardrobes**; diaries for **5 users** over 3–6 months | Not stated |

Audit protocol, per garment `[measured]`: (1) garment category, (2) acquisition method —
first-owner vs pre-owned, (3) active vs dormant, meaning used or not used in the prior 12
months.

## 4.2 Dormancy — how much of a wardrobe goes unworn

`[measured]`

| Source | Wardrobe size | Dormant | Pre-owned |
|---|---|---|---|
| WRAP 2022, UK | **118 items** | **26%** (≈31 items) | — |
| Vermeyen 2025, n=156 | **198** | **22%** | **2%** |
| Vermeyen merged, n=316 | **199** (SD **101**) | **27%** (SD **16**) | **5%** |
| PLATE 2025, n=30 | 169 | 19% (138 used, 81%) | — |
| Dutch MFA (Brouwer et al. 2026), citing this literature | — | "fairly consistent **20–30%** across categories" | — |

**Both Flanders figures must be carried.** They come from different samples — the 22% is the
2024 audit alone, the 27% is the merged set — and quoting only one hides the instability.

**Observed range: 44 to 434 garments** across 156 people (Vermeyen). de Wagenaar et al. 2022,
a global sample of 520, observed **30 to 713**.

**Scope is the reason WRAP and Flanders are not directly comparable.** WRAP's 118 includes
underwear, socks and hosiery — the very categories sitting at 12–20% dormancy, and also the
highest-count ones. They drag the UK average down. On outfit-relevant scope, use the Flanders
figures.

**Never use a point estimate for an individual.** SD 16 on a 27% mean, and a 10× range in
wardrobe size, mean the per-user dormant share is not predictable from the population. The
composer must discover it in dialogue, not assume it.

### An unresolved disagreement between instruments

WRAP finds **sharp** per-category variation in dormancy: skirts 44%, dresses 43% at the top;
underwear 12%, socks 17%, bras 20%, sweatshirts/hoodies/fleeces 22%, jeans 24% at the bottom.
The Dutch MFA reports it as **fairly flat at 20–30% across categories**. These are not
describing the same structure. Scope differences explain part of it — WRAP's low outliers are
exactly the categories Flanders excludes — but *part* is not *all*, and nobody has checked how
much. **The corpus's occasion-boundedness argument depends on the sharp version being correct.**

Per-person category counts from WRAP `[measured]`: 15 pairs of socks (2 unworn), 15 pieces of
underwear (2 unworn), 12 T-shirts (3 rarely worn), 9 shirts or blouses (about a third unworn).

## 4.3 Why garments go unworn — three independent gates

`[measured]` WRAP 2022, verified at the report's own wording. These are the three reasons, each
with the categories where it dominates:

1. **Kept for occasions only.** Dominant for **dresses**; frequent for skirts, shirts/blouses,
   formal trousers, coats/jackets.
2. **No longer a good or comfortable fit.** Frequent for jeans, formal trousers, skirts, shorts,
   jogging bottoms, T-shirts/polo/jersey tops, bras, underwear.
3. **Still liked, but not a priority.** Explicitly distinguished in the report from "no longer
   like it". Frequent for knitwear, sweatshirts/hoodies, T-shirts, jeans, coats/jackets,
   underwear.

**Why the three-way split matters operationally.** They call for three different interventions
and only one of them is a styling problem. Gate 1 is addressed by versatility — showing the
garment works outside its occasion. Gate 2 is a fit problem and no amount of composition fixes
it. Gate 3 is a salience problem — the garment is fine and liked, it simply never surfaces.
**A recommender that treats all dormancy as one phenomenon will apply the wrong lever to two
thirds of it.**

## 4.4 Longevity and wear intensity

### Years kept `[measured]` — WRAP 2022, with 2013 baseline where available

| Category | Years | 2013 |
|---|---|---|
| Coats / jackets (unpadded) | **> 6** | — |
| Dresses | 4.6 | 3.8 |
| Jeans | 4.0 | 3.0 |
| T-shirts | 4.0 | 3.3 |
| Underwear | 2.7 | — |
| Bras | 2.6 | — |

- **Pre-loved and vintage garments are kept ≈5.4 years — about 1.4 years longer than new.**
- **Repair adds ≈1.3 years.**

### Wears between washes `[measured]` — WRAP 2022

padded jackets/coats **≈17** · jeans **5.5** · T-shirts 2.6 · dresses 2.6 · skirts and blouses
**2.3**. Respondents aged 18–34 wash after fewer wears than older groups.

### Occasion-conditioned wear counts `[measured]` — Vermeyen 2026

The 2026 study measures service lifespan across **12 garment categories × 6 wear occasions × 3
metrics** (years, wears, washing cycles). **Three cells of that matrix are in hand:**

| Category × occasion | Kept | Worn | Washed |
|---|---|---|---|
| T-shirt, **informal** | 4 years | **33** | 18 |
| T-shirt, **formal** | 5 years | **9** | 6 |
| Coat, **informal** | 5 years | **136** | hardly ever |

Three things follow, and only the first is what the corpus expected:

1. **Occasion effect within a category: 3.7×** — and in the counter-intuitive direction, where
   the item kept *longer* is worn *less*. Service life and wear intensity are two separate axes.
2. **Category effect: at least 4.1×** (informal coat 136 vs informal t-shirt 33), running
   **opposite to price intuition**. The expensive outer layer is the most-worn object in the
   wardrobe, not the least. A CPW denominator that treats coats as occasion-wear because they
   are costly has the sign backwards.
3. **Interquartile ranges within garment types are large.** These are central tendencies over a
   heterogeneous population, not per-user predictions. Any denominator built on them must be
   distributional.

**The remaining ~213 cells were not obtained, and reading will not get them.** The article is
robots-excluded on ScienceDirect, the repository copy is account-gated, and the paper's own
data-availability statement releases publicly **only** the wardrobe-audit data — everything else
is "available on request". The next action is an email to the corresponding author
(V. Vermeyen, KU Leuven / Utrecht, project 3E211210), not another search.

## 4.5 Capsule numbers, and why no threshold survives

`[measured]` Vermeyen, Duyvejonck & Germeys, *From excess to essential*, PLATE 2025 — wardrobe
audit of 30 individuals in Flanders, each wardrobe reduced to only the garments deemed essential
for the coming year:

- 169 garments owned on average; **138 used in the past year (81%)**; **90 considered essential
  (53%)**.
- **Perceived essential need ranged from 36 to 275 garments — 28% to 98% of the current
  wardrobe.** A **7.6× spread.**
- **Combinability emerged as the single most important criterion** for selecting essential
  garments.
- Anticipated obstacles were both practical (shortages) and emotional (loss of joy).
- The thesis reports the related figure on the merged sample: **58% (SD 22) of a wardrobe is
  perceived as sufficient** for the coming year.

**Two consequences.**

**(a) The capsule constants are measurably indefensible as thresholds.** 33 pieces, 30 pieces,
15–20 pieces, 70/30 — all `[folkloric]`. When people are asked directly how many garments they
need, the answer spans 7.6×. No single number can be a threshold across that spread. The
demotion to `convention` is correct, and now rests on a measurement rather than on the absence
of one.

**(b) Graph density gains direct empirical support.** People performing the selection task
themselves ranked **combinability first** among their own criteria. That is not proof that
density predicts wear — it is evidence that density is what humans optimise when they do this
task by hand, which is the practitioner layer this project weights above cited theory.

## 4.6 The finding that underwrites orphan-rescue

`[measured]` Vermeyen et al. 2025, n=156, on the dormant stock specifically:

- **75% of dormant garments are in good enough condition for reuse.** They are not worn out.
  Three quarters of the unworn wardrobe is functionally fine clothing sitting idle.
- **Owners are unwilling to part with over half of their dormant garments — primarily because
  they believe the garments will prove useful in future.**
- **Only 2% of the wardrobe was pre-owned**, which the authors read as low demand for
  second-hand garments.

The authors' conclusion is pessimistic and, for their question, correct: **reactivation
potential is limited**, because owners will not release the stock and the resale market is thin.
Circular-economy policy aimed at moving dormant garments *out of* wardrobes hits a wall.

**For this project the same finding points the other way — and this inversion is `[inferred]`,
our argument, not the authors' finding.** Our product does not need the garment to leave the
wardrobe. The three facts describe precisely the conditions under which reactivation *in place*
is the right intervention: the stock exists, three quarters of it is wearable, and the owner has
already decided to keep it because she expects to use it later. What is missing is not
willingness and not condition — it is the occasion, the combination and the prompt. That is what
an outfit composer produces.

**Addressable pool, stated as a number:** ≈27% of the wardrobe is dormant, ≈75% of that is
serviceable, and >50% of it is being retained in explicit anticipation of future use.

### The gender question, and a competing explanation

`[measured]` Dunne 2012: an average of **7% of female participants' wardrobes and 47% of male
participants' wardrobes** are in regular use. Sample: 11 wardrobes for contents, 5 diarists.
A four-page note; "regular use" is an author-defined threshold. The direction is worth carrying;
the point values are not.

`[measured]` Vermeyen merged: **women own 235 garments on average, men 158** —
t(314) = 8.07, p < 0.001, **d = 0.91**. A large effect on wardrobe **stock**.

`[inferred]` The corpus explains the Dunne gap as a **utilisation** difference — women's
wardrobes being broader, more decorative, more occasion-bound, failing gates 1 and 3 at once.
The Flanders audit supplies a **stock-size** mechanism the corpus did not have: if women own
1.49× as many garments and dormancy rates are similar, the absolute orphan pool is already 1.49×
larger with no behavioural difference at all. Both mechanisms can operate. **Mark the
occasion-boundedness attribution as argument, not finding.**

This does not weaken orphan-rescue for a female-targeted product — it strengthens and re-bases
it. The pool is larger in absolute terms for a reason unrelated to taste.

### A sampling caution that points the wrong way

`[measured]` Vermeyen & Germeys, *Garment Reuse in Practice*, PLATE 2025 — a clothing swap in a
Belgian city: about **half** the garments brought to an in-person indirect-exchange swap found
new owners; **t-shirts and sweaters swapped more easily than trousers**. Comparing swap
participants (all women, 26–71) against the 78 women in the baseline audit: swappers had a
**similar wardrobe size, a much higher fraction of pre-owned garments, and — unexpectedly — a
slightly higher fraction of dormant garments.**

**Reuse-engaged behaviour does not predict lower dormancy.** Anyone reasoning that Ukraine's
second-hand saturation implies a particular dormancy or density profile should note that the one
direct test of that intuition came back pointing the wrong way.

## 4.7 The folklore ban-list

These numbers circulate widely in styling content and **none has a traceable primary source**.
They are `[folkloric]` and must never enter a rule at any force above `hint`, and never as a
threshold:

- **80/20** — "we wear 20% of our wardrobe 80% of the time". No study establishes this ratio for
  clothing. The measured figures are 22–27% dormant and 53–81% actively used, which is not the
  same claim and does not reduce to it.
- **"7 wears"** or **"10 wears"** as a purchase threshold.
- **#30wears** — an advocacy campaign target, not a measurement.
- **"82% of garments are worn fewer than 3 times"**.
- **Capsule counts** — 33, 30, 15–20 pieces; 70/30 splits. `[convention]` at best; see §4.5.

When one of these appears in a source, that source is repeating campaign material, and its other
numbers deserve the same scrutiny.

## 4.8 Wardrobe rules

| Rule | Content | Force |
|---|---|---|
| **R-USE-01** | A fifth to a third of a wardrobe goes unworn for a year. Replicated across method and country. Carry the spread, not the mean: 199 garments SD 101, 27% dormant SD 16, range 44–434. On outfit-relevant scope use the Flanders figures (excludes underwear/socks/accessories/shoes); WRAP's 26% is diluted by staples. **Never a point estimate for an individual.** | `strong · E` |
| **R-USE-02** | Dormancy is not one phenomenon. Three independent gates — occasion-only, fit, still-liked-but-not-a-priority — require three different interventions, and only the first and third are addressable by composition. | `strong · E` |
| **R-USE-03** | Versatility addresses gate 1 only. Salience addresses gate 3. **Nothing in the composer addresses gate 2**; a fit failure must be detected and excluded, not styled around. | `strong` |
| **R-USE-04** | The female/male utilisation gap is real (Dunne, n=11/5) but its attribution to occasion-boundedness is **argument, not finding** — a stock-size mechanism of comparable size exists (d = 0.91). | `default` |
| **R-USE-05** | The CPW denominator is occasion-conditioned, not a function of combinatorial reach. Mechanism established and large (3.7× within one category); **matrix not obtained** — 3 of ~216 cells. Nine of twelve composer-relevant categories have no wear prior. Gate stays replacement-only, off for exploration. | `soft` |
| **R-USE-06** | Graph density over item count as the wardrobe metric. Supported by practitioners' own stated criterion in a selection task (combinability ranked first, n=30), not only by decision-fatigue theory. Capsule counts remain conventions. | `strong` |
| **R-USE-07** | Second-hand engagement does **not** predict lower dormancy — the one direct test found swappers slightly *more* dormant. Any UA second-hand overlay must be measured, not reasoned from saturation. | `hint` |
| **R-USE-08** | Orphan-rescue is a first-class composer output. Measured base: ~27% of the wardrobe dormant, **~75% of it in reusable condition**, **>50% retained in explicit anticipation of future use**. *Where it breaks:* the source paper concludes reactivation potential is **limited** for circular-economy purposes (owners will not release stock; 2% pre-owned means thin resale demand). That conclusion is correct for policy aimed at moving garments out of wardrobes and does not transfer to reactivation in place — but **the inversion is our reading, not the authors' finding**. | `strong · E` |
| **R-USE-09** | Longevity priors, for replacement timing: coats >6 y, dresses 4.6, jeans 4.0, T-shirts 4.0, bras 2.6. Pre-loved garments are kept ~1.4 y longer than new; repair adds ~1.3 y. UK self-report; transfer to UA unverified. | `default` |


---

# PART 5 — RULE REGISTER

Every rule in this file, with force and the decision it changes. A rule with no before/after is
not a rule; none are listed without one.

| ID | Force | Decision it changes |
|---|---|---|
| R-FEED-01 | `hard` | Which field the parser reads as the grouping key — and whether it falls back silently |
| R-FEED-02 | `hard` | Whether `моделей` in a coverage report is interpretable at all |
| R-FEED-03 | `strong` | Whether an out-of-stock SKU counts toward slot coverage |
| R-FEED-04 | `strong` | Whether a bilingual or multi-value colour param is read, lost, or mangled |
| R-FEED-05 | `default` | Whether `verify.py` keeps its name witness on a `vendor.model` feed |
| R-FEED-06 | `strong` | Whether a colour name enters the working vocabulary on 6 designs or on 40 duplicate rows |
| R-FEED-07 | `default` | Whether a fit-matching layer gets built on a field that does not exist |
| R-FEED-08 | `default` | Whether a param-less feed with the colour in the title is visible to the live path at all |
| R-FP-01 | `default` | Whether category and attribute share a schema axis |
| R-FP-02 | `default` | Whether a missing attribute slot is logged as an extraction failure |
| R-FP-03 | `default` | Which holes in our attribute vocabulary get filled next |
| R-FP-04 | `hint` | Which attributes get a second, gated model call — and at what cost per SKU |
| R-FP-05 | `default` | How deep the taxonomy is allowed to nest |
| R-FP-06 | `hard` | Whether the extractor may ever be forced to produce a label |
| R-FP-07 | `default` | Whether nickname-class outputs ship without a confidence signal |
| R-FP-08 | `default` | Whether our attributes remain externally comparable |
| R-ONT-05 | `soft` | Whether garment parts enter the schema — justification (а) void, (б) sufficient |
| R-ONT-09 | `default` | **Acquisition path corrected**: brand size tables are scraped, never ingested |
| R-ONT-12 | `strong` | Open-world colour/size vocabulary — verified normatively, not inferred |
| R-USE-01 | `strong · E` | Whether the system assumes a dormant share per user or discovers it |
| R-USE-02 | `strong · E` | Whether dormancy gets one lever or three |
| R-USE-03 | `strong` | Whether a fit-failed garment is styled around or excluded |
| R-USE-04 | `default` | Whether the gender gap is stated as finding or as argument |
| R-USE-05 | `soft` | Whether the purchase gate fires on a wear forecast — currently it may not, outside t-shirts and coats |
| R-USE-06 | `strong` | Whether wardrobe health is measured by count or by density |
| R-USE-07 | `hint` | Whether a UA second-hand overlay is assumed or measured |
| R-USE-08 | `strong · E` | Whether orphan-rescue is a first-class output or a side effect |
| R-USE-09 | `default` | When the system suggests replacement rather than restyling |

**Demotions and corrections made in this pass, relative to the previous corpus:**

1. **R-ONT-04 `strong` → split.** "`group_id` is native to the UA YML feed" is **true for Prom,
   false for Rozetka**, where grouping happens marketplace-side and no key exists in the file.
2. **R-FP-04 `hard` → `hint`.** Regime transfer: evidence is from worn-on-body street imagery
   via a segmentation metric, applied to single-garment catalogue photography.
3. **R-ONT-05 reason (а) void.** Parts AP 19.3 does not support flattening; reason (б) does.
4. **R-ONT-09 acquisition assumption corrected.** Rozetka does not deliver size tables in the
   feed; they are manual spreadsheets submitted by support ticket.
5. **R-USE-05 held at `soft`.** An earlier draft of this audit claimed the CPW denominator was
   "seeded" on the strength of two cells. It was not. Three cells is still not a matrix.
6. **R-USE-08 `note` → `strong · E`.** Orphan-rescue acquires a measured base (75% serviceable,
   >50% deliberately retained).
7. **R-USE-07 added at `hint`** with the sign reversed from the corpus's intuition.

---

# PART 6 — WHAT WAS NOT VERIFIED

Reported as prominently as the findings.

**Not obtained, with the reason it is a wall rather than an unfinished search:**

- **The Vermeyen occasion × category × metric matrix.** 3 of ~216 cells. ScienceDirect
  robots-excluded; repository copy account-gated; data-availability statement releases only the
  wardrobe-audit portion publicly. **Next action is an email to the corresponding author, not a
  search.** Until then R-USE-05 stays `soft`.
- **Rozetka's «Довідники» (per-category characteristic and value dictionary) and «Правила
  групування» (per-category grouping rules).** Both behind a seller account. Everything in §1.1
  about parameter *types and separators* is public and verified; nothing about *which
  characteristic names apparel categories actually use* is available. `params.get("колір")`
  therefore remains a guess with a known shape rather than a looked-up name.
- **The «Reactivation Potential of Dormant Garments by Perceived Quality and Reason for Disuse»
  figure** in the open-access Flanders audit — the one figure that would break the 75%-reusable
  number down by *why* the garment is dormant, joining it to WRAP's three gates. It is in a
  freely available PDF and was not opened.
- **Fashionpedia's supplementary material**, holding per-super-class *not sure* rates and the
  full per-class AP breakdown. §3.5's argument rests on the main text's stated cause of *not
  sure* plus the image-composition statistics; the finer numbers could sharpen or complicate it.
- **The 19th apparel part.** 18 of 19 identified from the published figure.
- **Horoshop's YML specification.** The corpus attributes to Horoshop a native exact-colour vs
  filter-colour distinction and a "modifications" variant model. Neither verified. R-FEED-01's
  branch list is complete for Prom and Rozetka and **incomplete for Horoshop**.
- **Dahunsi & Dunne 2021 (RecSys) and Dahunsi 2023 (IJFDTE).** Paywalled. R-ONT-07's "156 years,
  no stable ontology" claim and the three-factor stylist model remain abstract-level.
- **WRAP's figure-level tables.** The report PDF is robots-disallowed at wrap.ngo; the three
  gates, the 44%/43% split and the longevity figures were verified from the report's own text
  via an accessible mirror and from WRAP's press material. The full category tables were not
  opened.
- **Ellen MacArthur Foundation 2017** (utilisation −36% over 15 years; UK 3.3 years; <1%
  closed-loop recycling) was **not re-verified in this pass** and is carried at the corpus's own
  confidence, not this file's.
- **ДСТУ 2027-92, УКТЗЕД, ДСТУ ГОСТ 31396:2011** — Ukrainian-language normative sources, outside
  the English-source scope of this pass.

**Reasoned but not observed:**

- **No feed was parsed.** Every defect D1–D10 is derived from reading specifications against
  code. None was reproduced against a real XML file. The D2 inflation factor of 4–7× is reasoned
  from Rozetka's one-offer-per-size mandate plus its named apparel grouping characteristic —
  **not measured**.
- **The category-concentration disagreement (§4.2) is unresolved.** Sharp (WRAP) vs flat (Dutch
  MFA). Scope explains part. Nobody has quantified how much. The corpus's occasion-boundedness
  argument depends on the sharp version.
- **No outcome validation of anything in this file.** Nothing here shows that fixing D1–D10
  produces better outfits, or that an occasion-conditioned denominator predicts wear. What it
  shows is that the coverage number is currently uninterpretable, that one rule's force was
  unearned, that one acquisition assumption was wrong, and that orphan-rescue has a measured
  base it previously lacked.

---

# PART 7 — WHAT TO RUN NEXT

## 7.1 One feed, six numbers

Everything in Parts 1–2 is reasoning about code from documents. It resolves in a single run and
needs no annotation. Take one Tier-A feed from the ingest backlog and report:

1. Total `offers`.
2. Share with a resolvable grouping key, **by branch**: `group_id` attribute / `<group_id>`
   child / `article` / reconstructed / none.
3. `моделей / sku` ratio inside each occupied slot — the direct measure of D2 inflation.
4. Share out of stock under the three-state read of R-FEED-03, and what removing them does to
   `частка_порожніх`.
5. Share of offers whose colour param is lost to D6 (`<value lang>` children) or split by D7
   (comma / `|` / `/`) or truncated by D8 (`<br/>`).
6. `лексикон` recomputed **per design** instead of per SKU: how many names lose `придатна=True`.

**Predictions recorded in advance.** On a Rozetka-format feed, branch (2) resolves to `none` for
the majority; ratio (3) lands between 4 and 7; at least a third of currently-`придатна` colour
names in (6) fail once duplicate photographs stop voting more than once.

**Falsifier:** if ratio (3) comes back near 1.0, D1 and D2 are wrong about this shop and the
published coverage numbers stand.

## 7.2 Sixty SKUs, four attributes

The extraction test in §3.6, with P1–P3 recorded. Replaces a borrowed reliability number with a
measured one in our own image regime, and either demotes or restores R-FP-04 on evidence.

## 7.3 One email

To V. Vermeyen (KU Leuven / Utrecht, project 3E211210), requesting the service-lifespan dataset.
It is the only route to the remaining ~213 matrix cells, and it is the difference between
R-USE-05 at `soft` and R-USE-05 usable across the nine composer categories that currently have
no wear prior.

## 7.4 One seller account

Rozetka's «Довідники» export would replace the guessed colour/size/material parameter names with
looked-up ones and would reveal the per-category grouping rules directly. It is the difference
between R-FEED-01's reconstruction branch being principled and being a guess.
