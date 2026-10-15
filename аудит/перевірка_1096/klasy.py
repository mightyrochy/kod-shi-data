import sys, os, json, copy, collections
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import оцінка_образу as О, суд_чеклісти as С
d0 = json.load(open(sys.argv[2])); е = d0["прогони"][0]["вердикти"][0]["етапи"]
d = dict(d0["спільне"]["вхід_прогону"], речі=е["речі"]["речі"], пікселі={}, сценарій_оцінки=е.get("сценарій_екрана") or {})
d.pop("каталог", None); О._виміри = lambda *а, **к: copy.deepcopy(е["суд"]["речі"])
лов = {}; _б = О._без_входу; О._без_входу = lambda о, с, р: (лов.setdefault("о", о), _б(о, с, р))[1]
суд = О.суд(d); F, T, _ = О._профіль(dict(d)); пал = С.входи_палітри(F, source=d.get("source") or "uncontrolled")
КЛАС = {**dict.fromkeys("print_budget print_dominant_hers accent_echo colours_in_her_pairings accent_surfaces_differ "
                        "one_metal metal_is_surface jewelry_kind_asked jewelry_scale necklace_off_neckline "
                        "accessory_edge_placement glove_sleeve_length tights_density tights_link repairable_shoes "
                        "grey_hair_eyes_lead face_colour_eye_side soft_palette_drama_by_lightness".split(), "A"),
        **dict.fromkeys("not_median_choice not_same_for_anyone passport_from_talk scheme_chosen "
                        "price_per_combinations repairs_not_opposed".split(), "B"),
        **dict.fromkeys("one_trend_item glasses_in_chroma refusal_reason_physical scale_to_person "
                        "one_silhouette_letter silhouette_decided layer_hems_apart one_sprezzatura".split(), "C"),
        **dict.fromkeys("shine_budget fabric_cut_formality formality_spread hem_off_widest_point".split(), "D"),
        **dict.fromkeys("near_face_weight weather_withstood".split(), "E"),
        **dict.fromkeys("neutrals_tone_or_step context_keeps_edge_colour".split(), "F")}
рядки_всі = [х.get("стан") for п in лов["о"]["чеклісти"].values() if isinstance(п, list) for х in п if isinstance(х, dict)]
print(dict(collections.Counter(рядки_всі)))
рядки = [О._ВМ.код_пункту(х.get("пункт")) for п in лов["о"]["чеклісти"].values() if isinstance(п, list)
         for х in п if isinstance(х, dict) and х.get("стан") == "без входу"]
print("без входу", len(рядки), dict(sorted(collections.Counter(КЛАС.get(к, "?") for к in рядки).items())),
      "| без_входу записів", len(суд["без_входу"]), "| рівень", суд["рівень"],
      "| сивина", пал["сивина"], "бік b* очей", пал["бік_b_очей"], "бік температури", пал["бік_температури"])
