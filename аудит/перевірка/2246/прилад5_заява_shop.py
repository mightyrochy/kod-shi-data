import os, sys, json
sys.path.insert(0, os.getcwd())
import внутрішня_мова as ВМ, мовний_шар as МШ
ід = "ж-00042@nyni.shop"
з = ВМ.заява("photo_shared_by_other_products", count=3,
             items=[dict(item_id=ід, slot=ВМ.код_або_невідомо("slot", "сукня"), shop="nyni.shop", unknown=[])])
п = МШ.промпт_повідомлень(МШ.розмітити_повідомлення({"к": {"kind": "card_unchecked", "statements": [з]}}))
print("перекладач повідомлень, заява photo_shared_by_other_products: повний id", п.count(ід), "| 'nyni.shop'", п.count("nyni.shop"))
i = п.find("ПОВІДОМЛЕННЯ:"); print(п[i:i+420])
