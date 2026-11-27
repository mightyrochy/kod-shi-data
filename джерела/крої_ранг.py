"""Ранг відомого крою в ярусі тіла."""
import outfit as O, feed

def _ранг_крою(r, ярус):
    """0 — усі крої речі в ярусі тіла; 2 — усі оцінені й жоден не в ярусі; 1 — нейтрально
    (причину називає `причина_рангу_крою`)."""
    if not ярус:
        return 1
    кр, _ = O.крої_слота(r)
    if not кр or any(к not in ярус["оцінені"] for к in кр):
        return 1
    в = sum(1 for к in кр if к in ярус["ярус"])
    return 0 if в == len(кр) else (2 if в == 0 else 1)

def причина_рангу_крою(r, ярус):
    """Код, чому ранг крою такий: `cut_in_body_tier` / `cut_below_body_tier` (0 / 2) або причина
    нейтральності — `no_body_tier`, `cut_unknown` (слова нема), `cut_word_outside_slot` (слово
    поза кроями слота, перекладу нема), `cut_word_of_other_part` (слово про іншу частину речі),
    `cut_not_scored` (крій слота, якого простір не оцінив),
    `cut_word_straddles_tier` (слово лягає на кілька кроїв, і ярус тіла їх розводить)."""
    if not ярус:
        return "no_body_tier"
    кр, прич = O.крої_слота(r)
    if прич in ("cut_unknown", "cut_word_outside_slot", "cut_word_of_other_part"):
        return прич
    if any(к not in ярус["оцінені"] for к in кр):
        return "cut_not_scored"
    р = _ранг_крою(r, ярус)
    return {0: "cut_in_body_tier", 2: "cut_below_body_tier"}.get(р, "cut_word_straddles_tier")
