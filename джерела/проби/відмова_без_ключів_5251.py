"""Рядок 5251: промпт мовної моделі для відмови K-IO-01 — чи несе він внутрішні імена полів («дрес_код»), які модель переписує жінці."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge, сценарій as СЦ

повід = {"відмова": СЦ.брак_сценарію_жінці()}
пр = json.loads(bridge.виклик("мова", {"повідомлення": повід}))["промпт"]
заява = next(р for р in пр.splitlines() if "no_scenario_fields" in р or "where she is going" in р)
print("заява в промпті:", заява[:420])
print("українські ключі (слова з «_» кирилицею) у промпті:", sorted(set(re.findall(r"[а-яіїєґ]+_[а-яіїєґ_]+", пр))))
