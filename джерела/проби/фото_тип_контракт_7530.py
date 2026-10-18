"""Синтетична сім’я #1450; фото-приймання pending."""
from фото_тип_синтетика import *

def contract():
    bundle = Ф.пакет_контракту()
    assert len(bundle["taxonomy"]["types"]) == 99 and len(bundle["taxonomy"]["slots"]) == 25
    assert bundle["hashes"]["taxonomy_sha256"] == "f720299e9b86f5141ccfdaafff9ed275f2971cadedc9cf8af48ec5f6fa36bbb0"
    r, _, _ = fixture()
    assert Ф.перевірити_запис(r)["status"] == "classified"
    bad = copy.deepcopy(r); bad["visible_item_type"]["item_type"] = "dress_generic"
    assert Ф.перевірити_запис(bad)["errors"] == ["observation_mismatch"]
    bad = copy.deepcopy(r); bad["producer"]["taxonomy_sha256"] = "f" * 64
    assert Ф.перевірити_запис(bad)["errors"] == ["contract_hash_mismatch"]
    bad = copy.deepcopy(r); bad["producer"]["kind"] = "catalog"
    assert Ф.перевірити_запис(bad)["status"] == "invalid"
    for raw in ('{"target":"unique","target":"ambiguous"}', '{"catalog_type":"shirt"}', 'NaN'):
        assert Ф.перевірити_відповідь(raw)["status"] == "invalid"
    for target, reason, status in (("ambiguous", "multiple_objects", "ambiguous"), ("not_visible", "not_visible", "unknown")):
        raw = json.dumps(dict(target=target, item_type="unknown", bbox=None, reason=reason))
        assert Ф.перевірити_відповідь(raw)["status"] == status
    for bbox in ([0, 0, 0, 2], [False, 0, 2, 2], [-1, 0, 2, 2]):
        assert Ф.перевірити_відповідь(json.dumps(dict(target="unique", item_type="shirt", bbox=bbox, reason=None)))["status"] == "invalid"

if __name__ == "__main__":
    contract()
    print("SYNTHETIC_ONLY contract: PASS; photo acceptance pending")
