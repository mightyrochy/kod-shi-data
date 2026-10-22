"""Синтетична сім’я #1450; фото-приймання pending."""
from фото_тип_синтетика import *

def projection():
    r, m, receipt = fixture()
    overlay = dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[r])
    result = Ф.проєкція_каталогу(overlay, m, receipt)
    assert result["records"]["synthetic"]["slot"] == "top"
    assert result["records"]["synthetic"]["target"] == "unique"
    assert result["records"]["synthetic"]["bbox"] == [0, 0, 1000, 1000]
    amb = dict(target="ambiguous", item_type="unknown", bbox=None, reason="multiple_objects")
    record = Ф.спостереження(json.dumps(amb), sku="synthetic", image_sha256="a"*64, image_url=r["image"]["url"], crop=None, model_id="synthetic", model_revision="fixture")
    assert Ф.проєкція(record, sku="synthetic", image_sha256="a"*64, image_url=r["image"]["url"])["reason"] == "multiple_objects"
    assert "measured" not in json.dumps(result)
    args = dict(sku=r["sku"], image_sha256="f" * 64, image_url=r["image"]["url"])
    assert Ф.проєкція(r, **args)["errors"] == ["image_mismatch"]
    assert Ф.проєкція_каталогу(overlay, m, None)["ledger"]["unprojected"] == 1
    bad = copy.deepcopy(receipt); bad["dataset_revision"] = "f" * 40
    assert Ф.перевірити_кадри(m, bad)["errors"] == ["capture_hash_mismatch"]
    bad = copy.deepcopy(m); bad["records"]["fixture"]["image_sha256"] = "f" * 64
    assert Ф.перевірити_кадри(bad, receipt)["status"] == "invalid"
    bad = copy.deepcopy(receipt); bad["verified_capture_ids"] = []
    assert Ф.проєкція_каталогу(overlay, m, bad)["ledger"]["unprojected"] == 1
    assert Ф.проєкція_каталогу(dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[r, r]), m, receipt)["records"] == {}
    for bad in (None, [], {"capture": {"id": []}}, dict(r, image=[])):
        assert Ф.проєкція_каталогу(dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[bad]), m, receipt)["records"] == {}
    controls = copy.deepcopy(m)
    controls["records"]["fixture"].update(sku=None, source_kind="service_control")
    accepted = dict(receipt, capture_manifest_sha256=sha(controls))
    assert Ф.перевірити_привязку(controls, accepted, capture_id="fixture", sku=None, image_url=r["image"]["url"])["status"] == "verified"
    forged = dict(r, capture=dict(id="fixture", manifest_sha256=sha(controls)))
    assert Ф.проєкція_каталогу(dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[forged]), controls, accepted)["ledger"]["controls_excluded"] == 1

if __name__ == "__main__":
    projection()
    print("SYNTHETIC_ONLY projection: PASS; photo acceptance pending")
