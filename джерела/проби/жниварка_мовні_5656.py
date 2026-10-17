# -*- coding: utf-8 -*-
"""Друкує структурний факт RAW → CLEAN без перезапису каталогу (5656)."""
import collections, gzip, hashlib, json, pathlib, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import чистка_каталогу as чистка


def вимір(шлях):
    """Читає XML/gzip й рахує чинні структурні двійники, без тлумачення назв."""
    байти = gzip.open(шлях, "rb").read() if шлях.endswith(".gz") else pathlib.Path(шлях).read_bytes()
    корінь = ET.fromstring(байти)
    офери = list(корінь.iter("offer"))
    return офери, {"sha256_xml": hashlib.sha256(байти).hexdigest(), "оферів": len(офери),
                    "мовних_пар_url_і_фото": len(чистка.мовні_двійники(корінь)),
                    "двійників_товару": len(чистка.двійники_товару(корінь))}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Потрібні два шляхи: RAW.xml[.gz] CLEAN.xml[.gz]")
    сирі, до = вимір(sys.argv[1])
    чисті, після = вимір(sys.argv[2])
    ід = lambda офери: [о.get("id") for о in офери]
    живі = set(ід(чисті))
    за_ід = {о.get("id"): о for о in сирі}
    зміни = collections.Counter()
    for о in чисті:
        старий = за_ід.get(о.get("id"))
        for поле in ("url", "vendorCode", "group_id"):
            знач = lambda в: в.get(поле) if поле == "group_id" else в.findtext(поле)
            зміни[поле] += старий is None or знач(о) != знач(старий)
    print(json.dumps({"ДО_RAW": до, "ПІСЛЯ_CLEAN": після,
                      "ід_CLEAN_відсутні_RAW": len(живі - set(ід(сирі))),
                      "порядок_лишених_ід_збережено": ід(чисті) == [і for і in ід(сирі) if і in живі],
                      "зміни_полів_ідентичності": dict(зміни)}, ensure_ascii=False, indent=2))
