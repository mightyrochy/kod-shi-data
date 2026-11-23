#!/usr/bin/env python3
"""Побудувати пошуковий індекс із перевіреної робочої HTML-збірки Люстерка.

Виклик: python3 build_index.py /шлях/до/index.html /шлях/до/catalog.json.gz
Збірка імпортує локальні модулі з указаного довіреного HTML для відтворення
того самого розбору фіду та готових записів рушія. Мережа під час роботи не потрібна.
"""
import argparse
import base64
import collections
import gzip
import hashlib
import html
import importlib
import io
import json
import math
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit
import zipfile


MODULES = re.compile(("const\\s+МОДУЛІ_ПОКАЗУ"+r'\s*=\s*"([a-zA-Z0-9+/=]+)"').encode())
COLORS = re.compile(r"#[a-fA-F0-9]{6}\Z")
STOP_TAGS = {"одяг", "наявність", "джерело", "приклад", "жіночий", "жіноча", "жіночі", "особливості", "one", "size"}
COLOR_NO_INFO = {"не названо", "невідомо", "невідомий", "не визначено", "не вказано", "відсутній", "уточнюйте"}
SLOTS = {
    "верх":"top", "низ":"bottom", "верхній_шар":"coat", "сукня":"dress", "взуття":"shoes",
    "сумка":"bag", "шарф":"scarf", "прикраси":"jewels", "браслет":"jewels", "сережки":"jewels", "каблучка":"jewels",
    "намисто":"jewels", "брошка":"jewels", "кольє":"jewels", "комплект":"set", "пояс":"belt",
    "головний_убір":"hat", "рукавички":"gloves", "шкарпетки":"socks", "білизна":"underwear", "окуляри":"eyewear",
}
MATERIAL = ("матеріал_родина","склад_основа","матеріал","склад","~склад","~матеріал","матеріал верху","матеріал_верху")

# Параметри надходять із XML жниварки, а не створюються модулями рушія.
# У повному каталозі 23.11.2026: свотч — 619 записів, наявність — 28 012.
ЗОВНІШНІ_ВХОДИ = {
    "свотч_hex": "param XML: магазинний свотч #rrggbb; запасний після виміряного колір_hex_фото",
    "наявність": "param XML: значення нема виключає товар; інакше зберігається тристановий available парсера",
}


def text(value):
    if isinstance(value, (list, tuple)):
        return ", ".join(filter(None, (text(v) for v in value)))
    if not isinstance(value, str):
        return ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def web_url(value):
    if not isinstance(value,str):
        return ""
    if value.startswith("//"):
        value="https:"+value
    try:
        target=urlsplit(value)
        if target.scheme in {"https","http"} and target.hostname and not target.username and not target.password:
            return value
    except ValueError:
        pass
    return ""


def load_modules(html_file):
    if zipfile.is_zipfile(html_file):
        return zipfile.ZipFile(html_file)
    with html_file.open("rb") as f:
        source=f.read()
    match=MODULES.search(source)
    if not match:
        raise ValueError("У HTML відсутній пакет МОДУЛІ_ПОКАЗУ.")
    return zipfile.ZipFile(io.BytesIO(base64.b64decode(match.group(1),validate=True)))


def extract_runtime(package, directory):
    # Для нативного читача потрібні Python-джерела, корпус і вкладений фід.
    for member in package.infolist():
        relative=Path(member.filename)
        if relative.parent!=Path(".") or relative.suffix not in {".py",".xml",".gz",".tsv",".json"}:
            continue
        (directory/relative).write_bytes(package.read(member))
    for name in ("каталог_brief.xml","каталог_таблиця.json.gz","фід_розбір.py","таблиця_каталогу.py"):
        if not (directory/name).is_file():
            raise ValueError("У пакеті відсутній файл "+name)


def tags_for(offer, native, raw_slot, material):
    params=offer["параметри"]
    fields=[raw_slot, native.get("тип"), native.get("рід_тканини_слово"), native.get("волокно"),material,
            native.get("текстура"),native.get("крій"),native.get("рукав_слово"),native.get("метал"),
            native.get("довжина_рівень"), native.get("візерунок"),native.get("виріз_тип")]
    fields.extend(params.get(k) for k in ("тип","категорія_магазину","матеріал_родина","сезон","~сезон","~теги (магазин)",
                                          "силует","довжина","рукав_рівень","посадка","склад","~матеріал"))
    terms={}
    for field in fields:
        for token in re.findall(r"[a-zA-Zа-яА-ЯєіїґЄІЇҐ]+(?:[’'][a-zA-Zа-яА-ЯєіїґЄІЇҐ]+)?",text(field).lower()):
            if len(token)>=3 and token not in STOP_TAGS:
                terms[token]=None
            if len(terms)==32:
                return " ".join(terms)
    return " ".join(terms)


def best_material(offer, native):
    params=offer["параметри"]
    for candidate in (native.get("матеріал"),native.get("рід_тканини_слово"),*(params.get(k) for k in MATERIAL)):
        v=text(candidate)
        if v and len(v)<=220 and v.lower() not in {"невідомо","інше","інша"}:
            return v
    return ""


def prepare(offer, native, blocked):
    params=offer["параметри"]
    identifier=offer["id"]
    original_slot=text(native.get("слот") or params.get("слот") or offer.get("категорія"))
    slot=SLOTS.get(original_slot, "other")
    name=text(native.get("назва_показу") or offer.get("назва_показу") or offer["назва"])
    shop=text(offer.get("магазин"))
    native_hue=text(native.get("колір_назва") or offer.get("колір_назва"))
    hue="" if native_hue.lower() in COLOR_NO_INFO else native_hue
    swatch=""
    for value in (native.get("колір_hex_фото"),params.get("свотч_hex")):
        if isinstance(value,str) and COLORS.fullmatch(value.strip()):
            swatch=value.strip().lower()
            break
    native_price=offer.get("ціна")
    price=None
    if isinstance(native_price,(int,float)) and math.isfinite(native_price) and native_price>0:
        price=int(native_price) if float(native_price).is_integer() else native_price
    images=[]
    if not (native.get("без_показу") or offer.get("без_показу")):
        # Порожній список у готовій картці теж є рішенням рушія.
        source=native.get("фото", offer.get("фото")) or []
        for raw in source:
            image=web_url(raw)
            if image and image not in blocked.get(shop,{}) and image not in images:
                images.append(image)
            if len(images)==2:
                break
    available=offer.get("available")
    named_status=text(params.get("наявність"))
    if named_status=="нема":
        available=False
    material=best_material(offer,native)
    harvested=text(params.get("знято"))
    return [identifier,name,slot,original_slot,shop,price,swatch,hue,web_url(offer.get("url")),images,
            tags_for(offer,native,original_slot,material), material, available, harvested, bool(native)]


def order_rows(rows):
    # Початкова полиця показує різні категорії і крамниці. Порівнянні кадри та ціни — першими.
    buckets=collections.defaultdict(lambda:collections.defaultdict(collections.deque))
    rows.sort(key=lambda r:(r[12] is False,not r[9], r[5] is None, r[4], r[0]))
    for row in rows:
        buckets[row[2]][row[4]].append(row)
    priority=["dress","top","bottom","coat","shoes","bag","jewels","scarf","set","belt","hat"]
    slots=list(dict.fromkeys(priority+sorted(buckets)))
    brand_lists={s:collections.deque(sorted(buckets[s],
                 key=lambda b:(not bool(buckets[s][b][0][9]),len(buckets[s][b])<10,b))) for s in slots if s in buckets and buckets[s]}
    recent=collections.deque(maxlen=7)
    ordered=[]
    while brand_lists:
        for slot in slots:
            if slot not in brand_lists:
                continue
            brands=brand_lists[slot]
            for _ in range(len(brands)):
                if brands[0] not in recent:
                    break
                brands.rotate(-1)
            brand=brands.popleft()
            items=buckets[slot][brand]
            ordered.append(items.popleft())
            recent.append(brand)
            if items:
                brands.append(brand)
            if not brands:
                del brand_lists[slot]
    return ordered


def build(html_file, output, module=None):
    with tempfile.TemporaryDirectory(prefix="mirror-index-") as tmp:
        runtime=Path(tmp)
        with load_modules(html_file) as package:
            extract_runtime(package,runtime)
        sys.path.insert(0,str(runtime))
        try:
            parser=importlib.import_module("фід_розбір")
            table=importlib.import_module("таблиця_каталогу")
            xml=runtime/"каталог_brief.xml"
            offers,_=parser.читати_yml(xml)
            with gzip.open(runtime/"каталог_таблиця.json.gz","rt",encoding="utf-8") as stream:
                prepared=table.відновити(json.load(stream),offers)["каталог"]
            with gzip.open(runtime/"каталог_службові_кадри.json.gz","rt",encoding="utf-8") as stream:
                blocked=json.load(stream)
            native={n["id"]:n for n in prepared}
            rows=order_rows([prepare(o,native.get(o["id"],{}),blocked) for o in offers])
            xml_sha=hashlib.sha256(xml.read_bytes()).hexdigest()
        finally:
            sys.path.remove(str(runtime))
    if len({r[0] for r in rows})!=len(rows):
        raise ValueError("У фіді є повторюваний ідентифікатор.")
    meta={"count":len(rows),"engineRecords":len(native),"shops":len({r[4] for r in rows}),"currency":"UAH",
          "source":"МОДУЛІ_ПОКАЗУ/каталог_brief.xml","feedSha256":xml_sha,"buildSha256":hashlib.sha256(html_file.read_bytes()).hexdigest()}
    stats={"withoutImage":sum(not r[9] for r in rows),"withoutPrice":sum(r[5] is None for r in rows),
           "withoutShop":sum(not r[4] for r in rows),"withoutUrl":sum(not r[8] for r in rows),"withoutSwatch":sum(not r[6] for r in rows),
           "withoutHue":sum(not r[7] for r in rows),"withoutMaterial":sum(not r[11] for r in rows),"availabilityUnknown":sum(r[12] is None for r in rows)}
    meta["coverage"]=stats
    packed=json.dumps({"meta":meta,"rows":rows},ensure_ascii=False,separators=(",",":")).encode("utf-8")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("wb") as file:
        with gzip.GzipFile(filename="",fileobj=file,mode="wb",compresslevel=9,mtime=0) as compressed:
            compressed.write(packed)
    if module is not None:
        js=module.read_text(encoding="utf-8")
        updated,count=re.subn(r"(const initialCount = )\d+(; // Значення з build_index\.py\.)",
                              lambda m: m[1]+str(meta["count"])+m[2],js)
        if count!=1:
            raise ValueError("У модулі відсутнє однозначне поле кількості карток.")
        module.write_text(updated,encoding="utf-8")
    print(json.dumps({**meta,"bytes":output.stat().st_size},ensure_ascii=False))


if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("production_html",type=Path)
    args.add_argument("output_gzip",type=Path)
    args.add_argument("--module",type=Path,help="Оновити лічильник у пошуковому JavaScript для наступної збірки.")
    parsed=args.parse_args()
    module=parsed.module or (parsed.output_gzip.parent/"search.js")
    build(parsed.production_html.resolve(),parsed.output_gzip.resolve(),module if module.is_file() else None)
