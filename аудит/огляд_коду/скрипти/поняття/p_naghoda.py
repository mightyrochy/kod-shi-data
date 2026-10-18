import sys, json, re; sys.path.insert(0,".")
import протокол as П, внутрішня_мова as ВМ, паспорт_нагоди as ПН, формальність as Ф, сценарій as С
def keys(x): return sorted(x) if isinstance(x,(dict,set,frozenset,list,tuple)) else x
print("ВИПАДОК type", type(П.ВИПАДОК).__name__, list(П.ВИПАДОК)[:40] if hasattr(П.ВИПАДОК,'__iter__') else '')
for k in ("нагода","опади","рух","дрес_код","увага","мета","намір","intent"):
    v = П.ВИПАДОК.get(k) if isinstance(П.ВИПАДОК, dict) else None
    print("ВИПАДОК[%s]"%k, v if not isinstance(v,dict) else {kk:vv for kk,vv in v.items() if kk in ('значення','enum','тип')})
print("ВМ occasion", ВМ.ТАБЛИЦЯ["occasion"])
print("ВМ precip", ВМ.ТАБЛИЦЯ["precipitation"])
for k in ВМ.ТАБЛИЦЯ:
    if re.search("attent|intent|goal|zone|formal|weather|wind|season|temper|slot|silhou|cut", k): print("ВМ", k, ВМ.ТАБЛИЦЯ[k])
print("ПН МІСЦЕ_ПЛИТКИ_НАГОДИ", ПН.МІСЦЕ_ПЛИТКИ_НАГОДИ)
print("ПН вечірні", ПН._ВЕЧІРНІ_НАГОДИ, "ходити", ПН._ХОДИТИ_НАГОДИ)
print("Ф.НАГОДА", sorted(Ф.НАГОДА)); print("Ф.МІСЦЯ", sorted(Ф.МІСЦЯ_ДІАПАЗОНИ))
