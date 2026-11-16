#!/usr/bin/env python3
"""Збирає альбом взірців із файлів даних.

  python3 аудит/айдентика/взірці/зібрати_альбом.py

Читає `паспорти.json` (джерело, права, автор знімка, палітра з пікселів), `дані/NN_*.json` (аркуш напрямку: взірці,
побачене, сенси), `дані/перенесення/*.html` (фрагменти екрана) і `дані/99_висновок.json`. Пише
`../альбом_взірців.html` і `джерела.md`. Зображення — окремими файлами поруч, рядком у HTML їх нема.
"""
import glob, html, json, os, re

ТУТ = os.path.dirname(os.path.abspath(__file__))
ДАНІ = os.path.join(ТУТ, "дані")
П = json.load(open(os.path.join(ТУТ, "паспорти.json"), encoding="utf8"))
E = html.escape
ВИДИ = {"першоджерело": "першоджерело", "побут": "як річ живе", "сучасне": "сучасне перенесення", "невдале": "невдале"}


def абзаци(xs, тег="li"):
    return "".join(f"<{тег}>{розмітка(x)}</{тег}>" for x in xs)


def розмітка(s):
    """Текст даних: екранування, #HEX → зразок кольору, **жирне**, `код`."""
    s = E(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"#([0-9A-Fa-f]{6})\b", r'<span class="hx"><i style="background:#\1"></i>#\1</span>', s)


def кольори(пари):
    return '<div class="sw">' + "".join(
        f'<span><i style="background:{E(h)}"></i><b>{E(h)}</b> {E(n)}</span>' for h, n in пари) + "</div>"


def стрічка(палітра):
    """Палітра з пікселів усього знімка: ширина смужки — частка площі."""
    return '<div class="strip" title="кольори всього знімка, ширина — частка площі">' + "".join(
        f'<i style="background:{h};flex:{max(p, 1)}" title="{h} · {p} %"></i>' for h, p in палітра) + "</div>"


def профіль(d):
    """Схема будови: частка кольору узору по смугах уздовж речі."""
    v = d["дані"]
    кол = d.get("колір", "#A8423F")
    осі = d.get("вісь", "згори вниз")
    смуги = "".join(f'<i style="width:{x}%;background:{кол}" title="смуга {i + 1}: {x} %"></i>' for i, x in enumerate(v))
    return (f'<div class="prof"><div class="bars">{смуги}</div>'
            f'<p>{розмітка(d["підпис"])} Смуг {len(v)}, {E(осі)}; довжина риски — частка узору в смузі.</p></div>')


def взірець(v):
    p = П[v["id"]]
    вид = ВИДИ[v["вид"]]
    частини = [f'<figure class="vz {E(v["вид"])}" id="vz-{E(v["id"])}">',
               f'<a class="im" href="{E(p["сторінка"])}"><img src="взірці/{E(p["файл"])}" alt="{E(v["назва"])}"></a>',
               '<figcaption>',
               f'<span class="kind">{E(вид)}</span><h4>{E(v["назва"])}</h4>',
               f'<p class="pass">{розмітка(v["паспорт"])}</p>',
               f'<p class="src">Джерело: <a href="{E(p["сторінка"])}">сторінка файлу</a> · знімок: {E(p["автор_знімка"] or "невідомо")} · '
               f'права: {E(p["права"])} · підпис на сторінці: «{E(короткий(p["опис_джерела"]))}»</p>',
               "<h5>Побачене</h5><ul>" + абзаци(v["побачене"]) + "</ul>"]
    if v.get("виміри"):
        частини.append(f'<p class="mes"><b>Виміри.</b> {розмітка(v["виміри"])}</p>')
    if v.get("схема"):
        частини.append(профіль(v["схема"]))
    if v.get("кольори"):
        частини.append("<h5>Колір із пікселів</h5>" + кольори(v["кольори"]))
    частини.append(стрічка(p["палітра"]))
    if v.get("впізнають"):
        частини.append(f'<p class="rec"><b>За чим упізнають.</b> {розмітка(v["впізнають"])}</p>')
    частини.append("</figcaption></figure>")
    return "".join(частини)


def короткий(s, n=230):
    s = re.sub(r"^(Українська|English|Русский|Polski): ", "", s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def посилання(v):
    вид = ВИДИ[v["вид"]]
    адреси = f'<a href="{E(v["сторінка"])}">сторінка джерела</a>'
    if v.get("зображення"):
        адреси += f' · <a href="{E(v["зображення"])}">зображення</a>'
    return (f'<div class="ln {E(v["вид"])}"><span class="kind">{E(вид)} · лише посиланням</span><h4>{E(v["назва"])}</h4>'
            f'<p class="pass">{E(v.get("автор", "невідомо"))}{", " + E(v["рік"]) if v.get("рік") else ""}. {адреси}. '
            f'Права: {E(v["права"])}.</p><p>{розмітка(v["побачене"])}</p></div>')


def перенесення(t):
    фрагмент = open(os.path.join(ДАНІ, "перенесення", t["файл"]), encoding="utf8").read()
    звідки = "; ".join(f'<a href="#vz-{E(i)}">{E(НАЗВИ.get(i, i))}</a>' if i in П else E(i) for i in t["зі_взірця"])
    return (f'<div class="tr"><div class="frag">{фрагмент}</div><div class="why"><h4>{E(t["назва"])}</h4>'
            f'<p class="from">зі взірця: {звідки}</p><ul>{абзаци(t["пояснення"])}</ul></div></div>')


def аркуш(d):
    ч = [f'<section class="sheet" id="{E(d["id"])}"><header><span class="no">{d["n"]:02d}</span>'
         f'<h2>{E(d["назва"])}</h2><p class="sub">{E(d["підзаголовок"])}</p></header>',
         f'<div class="said"><p><b>Що було в текстах.</b> {розмітка(d["сказано"])}</p>'
         f'<p><b>Чого там не видно.</b> {розмітка(d["не_показано"])}</p></div>']
    if d.get("не_знайдено"):
        ч.append(f'<p class="nf"><b>Не знайдено.</b> {розмітка(d["не_знайдено"])}</p>')
    ч += [взірець(v) for v in d.get("взірці", [])]
    if d.get("посилання"):
        ч.append('<div class="lns">' + "".join(посилання(v) for v in d["посилання"]) + "</div>")
    ч.append('<div class="sense"><div><h3>Візуальний сенс</h3><ul>' + абзаци(d["візуальний"]) + "</ul></div>"
             '<div><h3>Функціональний сенс для Люстерка</h3><ul>' + абзаци(d["функціональний"]) + "</ul></div></div>")
    if d.get("перенесення"):
        ч.append("<h3>Перенесення поруч зі взірцем</h3>" + "".join(перенесення(t) for t in d["перенесення"]))
    ч.append('<div class="no-take"><h3>Чого не брати</h3><ul>' + абзаци(d["не_брати"]) + "</ul></div></section>")
    return "".join(ч)


def висновок(w):
    рядки = "".join(
        "<tr>" + f'<th><a href="#{E(r["id"])}">{E(r["напрямок"])}</a></th>' + "".join(
            f"<td>{розмітка(r[k])}</td>" for k in ("впізнаваність", "сила", "з_фото", "робота")) + "</tr>" for r in w["таблиця"])
    return ('<section class="sheet" id="vysnovok"><header><span class="no">∑</span><h2>Висновок</h2>'
            f'<p class="sub">{E(w["підзаголовок"])}</p></header>'
            '<div class="tblw"><table><thead><tr><th>Напрямок</th><th>Упізнаваність без слів</th><th>Художня сила</th>'
            '<th>Поруч із фото одягу</th><th>Яку роботу несе</th></tr></thead><tbody>' + рядки + "</tbody></table></div>"
            + ("<h3>Чи змінило висновок дороблене 16.11</h3><ul>" + абзаци(w["доповнення"]) + "</ul>" if w.get("доповнення") else "") +
            "<h3>Що розвивати</h3><ul>" + абзаци(w["розвивати"]) + "</ul>"
            "<h3>Чого бракує, щоб вони стали мовою продукту</h3><ul>" + абзаци(w["бракує"]) + "</ul>"
            "<h3>Що відкласти</h3><ul>" + абзаци(w["відкласти"]) + "</ul>"
            "<h3>Не знайдено й не перевірено</h3><ul>" + абзаци(w["не_перевірено"]) + "</ul></section>")


СТИЛЬ = """
:root{--p:#F3EEE5;--k:#2B2521;--m:#6B5F56;--l:#D9CFC2;--a:#8E3B36;--w:#FBF8F2}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--p);color:var(--k);font:16px/1.55 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--a);text-underline-offset:2px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.top{padding:56px 0 28px;border-bottom:1px solid var(--l)}
.top h1{font:400 44px/1.1 Georgia,"Times New Roman",serif;margin:0 0 14px;letter-spacing:-.01em}
.top p{max-width:760px;margin:0 0 10px;color:var(--m)}
nav{display:flex;flex-wrap:wrap;gap:6px 8px;padding:18px 0 4px}
nav a{font-size:14px;text-decoration:none;color:var(--k);border:1px solid var(--l);padding:4px 10px;border-radius:2px;background:var(--w)}
nav a b{color:var(--a);font-weight:600;margin-right:5px}
.sheet{padding:54px 0 34px;border-bottom:1px solid var(--l)}
.sheet>header{display:grid;grid-template-columns:auto 1fr;column-gap:18px;align-items:baseline;margin-bottom:18px}
.sheet .no{font:400 44px/1 Georgia,serif;color:var(--a);grid-row:span 2}
.sheet h2{font:400 34px/1.1 Georgia,serif;margin:0}
.sheet .sub{margin:4px 0 0;color:var(--m);font-style:italic}
h3{font:400 23px/1.2 Georgia,serif;margin:34px 0 10px}
h4{font-size:17px;line-height:1.3;margin:4px 0 6px}
h5{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--m);margin:14px 0 4px}
ul{margin:0;padding-left:20px}li{margin:0 0 7px}
.said{background:var(--w);border-left:3px solid var(--l);padding:12px 16px;max-width:900px;color:var(--m);font-size:15px}
.said p{margin:0 0 6px}.said b{color:var(--k)}
.nf{background:#EFE3D0;padding:10px 14px;max-width:900px}
.vz{display:grid;grid-template-columns:minmax(220px,340px) 1fr;gap:26px;margin:30px 0 0;padding-top:26px;border-top:1px dotted var(--l)}
.vz .im{display:block;align-self:start;position:sticky;top:12px}
.vz img{display:block;width:100%;max-height:78vh;object-fit:contain;object-position:top;background:#E9E2D6}
.kind{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--a)}
.невдале .kind{color:#7A6A00}
.pass{margin:0 0 6px}.src{font-size:13px;color:var(--m);margin:0 0 4px}
.mes,.rec{font-size:15px;margin:12px 0 0}.mes{color:var(--m)}
.sw{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:14px}
.sw span{display:inline-flex;align-items:center;gap:6px}
.sw i,.hx i{display:inline-block;width:22px;height:22px;border:1px solid rgba(0,0,0,.18)}
.sw b{font:500 13px ui-monospace,Menlo,Consolas,monospace}
.hx{white-space:nowrap;font:13px ui-monospace,Menlo,Consolas,monospace}.hx i{width:11px;height:11px;margin-right:3px;vertical-align:-1px}
.strip{display:flex;height:10px;margin-top:10px;max-width:420px}.strip i{display:block}
.prof{margin-top:10px;max-width:520px}.prof .bars{display:flex;flex-direction:column;gap:1px;background:var(--w);padding:6px;border:1px solid var(--l)}
.prof .bars i{display:block;height:4px;min-width:1px}.prof p{font-size:13px;color:var(--m);margin:4px 0 0}
.lns{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:26px}
.ln{background:var(--w);border:1px solid var(--l);padding:14px 16px;font-size:15px}.ln p{margin:0 0 6px}
.sense{display:grid;grid-template-columns:1fr 1fr;gap:10px 40px}
.tr{display:grid;grid-template-columns:minmax(280px,400px) 1fr;gap:26px;margin:18px 0 26px;align-items:start}
.frag{background:#FFFDF9;border:1px solid var(--l);padding:0;overflow:hidden}
.why .from{font-size:13px;color:var(--m);margin:0 0 6px}
.no-take{max-width:900px}.no-take li{color:var(--m)}
.tblw{overflow-x:auto}table{border-collapse:collapse;font-size:14px;min-width:760px}
th,td{border-bottom:1px solid var(--l);padding:8px 10px;text-align:left;vertical-align:top}
thead th{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--m)}
footer{padding:26px 0 60px;color:var(--m);font-size:14px}
@media(max-width:760px){.top h1{font-size:32px}.sheet h2{font-size:27px}.sheet .no{font-size:32px}
 .vz,.tr,.sense{grid-template-columns:1fr}.vz .im{position:static}.vz img{max-height:70vh}}
"""


НАЗВИ = {}


def головна():
    аркуші = [json.load(open(f, encoding="utf8")) for f in sorted(glob.glob(os.path.join(ДАНІ, "[0-8]*.json")))
              if not os.path.basename(f).startswith("00_")]
    НАЗВИ.update({v["id"]: v["назва"] for d in аркуші for v in d.get("взірці", [])})
    шлях_висновку = os.path.join(ДАНІ, "99_висновок.json")
    w = json.load(open(шлях_висновку, encoding="utf8")) if os.path.exists(шлях_висновку) else None
    шапка = json.load(open(os.path.join(ДАНІ, "00_шапка.json"), encoding="utf8"))
    стиль_перенесень = open(os.path.join(ДАНІ, "перенесення", "стиль.css"), encoding="utf8").read()
    нав = "".join(f'<a href="#{E(d["id"])}"><b>{d["n"]:02d}</b>{E(d["назва"])}</a>' for d in аркуші)
    if w:
        нав += '<a href="#vysnovok"><b>∑</b>Висновок</a>'
    сторінка = ("<!doctype html><html lang=\"uk\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                f"<title>{E(шапка['назва'])}</title><style>{СТИЛЬ}{стиль_перенесень}</style></head><body><div class=\"wrap\">"
                f"<div class=\"top\"><h1>{E(шапка['назва'])}</h1>" + абзаци(шапка["вступ"], "p") + f"<nav>{нав}</nav></div>"
                + "".join(аркуш(d) for d in аркуші) + (висновок(w) if w else "")
                + "<footer>" + абзаци(шапка["низ"], "p") + "</footer></div></body></html>\n")
    open(os.path.join(ТУТ, "..", "альбом_взірців.html"), "w", encoding="utf8").write(сторінка)

    # джерела.md
    r = ["# Взірці: джерела й права", "",
         "Збирає `зібрати_альбом.py` з `паспорти.json` і `дані/`. У репозиторії лежать лише зменшені копії зображень, для "
         "яких сторінка джерела прямо називає вільні права; решта — посиланням.", "",
         "## Зображення в репозиторії", "",
         "| файл | аркуш | що це (підпис сторінки джерела) | автор знімка | права | сторінка джерела |", "|---|---|---|---|---|---|"]
    де = {v["id"]: d["назва"] for d in аркуші for v in d.get("взірці", [])}
    for i, p in П.items():
        if i not in де:
            continue
        r.append(f'| `{p["файл"]}` | {де[i]} | {короткий(p["опис_джерела"], 160).replace("|", "/")} | '
                 f'{(p["автор_знімка"] or "невідомо").replace("|", "/")} | {p["права"]} | <{p["сторінка"]}> |')
    r += ["", "## Лише посиланням", "", "| аркуш | що це | автор, рік | права | сторінка джерела |", "|---|---|---|---|---|"]
    for d in аркуші:
        for v in d.get("посилання", []):
            r.append(f'| {d["назва"]} | {v["назва"]} | {v.get("автор", "невідомо")}{", " + v["рік"] if v.get("рік") else ""} | '
                     f'{v["права"]} | <{v["сторінка"]}> |')
    open(os.path.join(ТУТ, "джерела.md"), "w", encoding="utf8").write("\n".join(r) + "\n")
    зайві = sorted(set(П) - set(де))
    print("аркушів", len(аркуші), "взірців із файлом", len(де), "лише посиланням",
          sum(len(d.get("посилання", [])) for d in аркуші), "| паспорти без аркуша:", зайві or "нема")


головна()
