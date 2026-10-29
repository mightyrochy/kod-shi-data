import os, sys, json
sys.path.insert(0, os.getcwd())
import statements as З, внутрішня_мова as ВМ, мовний_шар as МШ
ід, назва = "ж-00042@nyni.shop", "Dress Podyh Beige"
з = ВМ.заява("scarf_size_unknown", item=ВМ.вільний(назва), item_id=ід)
п = МШ.промпт_повідомлень(МШ.розмітити_повідомлення({"к": {"kind": "card_scheme", "statements": [з]}}))
print("перекладач повідомлень: назва", п.count(назва), "| повний id", п.count(ід), "| gepur/nyni-хвіст", п.count("@"))
