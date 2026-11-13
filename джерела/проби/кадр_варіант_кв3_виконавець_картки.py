"""Виконавець: колір і наявність картки — з даних її варіанта, а не з голови списку чи зведення. Друкує факт."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "zhnyvarka"))
import виконавець as в

def вар(опції, кольори, розміри, нема=()):
    return {"id": 1, "handle": "h", "title": "Сукня", "options": [{"name": "Колір", "position": 1, "values": кольори}, {"name": "Розмір", "position": 2, "values": розміри}],
            "variants": [{"id": 10 * i + j, "option1": к, "option2": р, "available": (к, р) not in нема} for i, к in enumerate(кольори) for j, р in enumerate(розміри)]}
def ld(оферти, sku="B"):
    return json.dumps({"@type": "Product", "name": "Сукня", "sku": sku, "offers": оферти}, ensure_ascii=False)
def дом(оферти, опції=()):
    html = '<script type="application/ld+json">%s</script>' % ld(оферти)
    к = в.картка_з_dom("https://s.test/p/1", html, {"opts": list(опції)}, {"назва": "Сукня", "артикул": "B"})
    return (к["колір"], к["наявність"])
о = lambda sku, ok: {"sku": sku, "url": "https://s.test/p/1?v=" + sku, "availability": "https://schema.org/" + ok}
два = [о("A", "InStock"), о("B", "OutOfStock")]
woo = {"id": 1, "name": "Сукня", "attributes": [{"name": "Колір", "terms": [{"name": "Чорний"}, {"name": "Білий"}]}],
       "variations": [{"id": 5, "attributes": [{"name": "Колір", "value": "Чорний"}]}, {"id": 6, "attributes": [{"name": "Колір", "value": "Білий"}]}]}
print("shopify 2 кольори, один розмір нема:", (lambda к: (к["колір"], к["наявність"]))(в.картка_з_shopify("https://s.test", вар(0, ["Чорний", "Білий"], ["S", "M"], {("Білий", "S")}))))
print("shopify 1 колір:", (lambda к: (к["колір"], к["наявність"]))(в.картка_з_shopify("https://s.test", вар(0, ["Чорний"], ["S", "M"]))))
print("woo 2 варіації кольору:", в.картка_з_woo("https://s.test", woo)["колір"] or "невідомо")
print("dom, 2 оферти (A є, B нема), сторінка B:", дом(два))
print("dom, 1 оферта:", дом(о("B", "InStock")))
print("dom, опції Чорний/Білий без рядка кольору:", дом(о("B", "InStock"), ["Чорний", "Білий"]))
три_розміри = [{"price": "1", "availability": "https://schema.org/" + x} for x in ("InStock", "OutOfStock", "InStock")]
_к = в.картка_з_dom("https://s.test/p/1", '<script type="application/ld+json">%s</script>' % ld(три_розміри), {"rows": [["Колір", "Чорний"]]}, {"назва": "Сукня", "артикул": "B"})
print("dom, 3 оферти розмірів без sku/url, рядок «Колір: Чорний»:", (_к["колір"], _к["колір_джерело"], _к["наявність"]))
