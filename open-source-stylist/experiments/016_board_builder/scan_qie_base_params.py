"""E-016 — tabulate the QIE sampler config actually used by every combined-graph qie_base PNG,
to see the swept range and whether the standalone-good config (union 1.0 / steps 20 / cfg 4.0) was
ever run in the combined graph."""
import json
from pathlib import Path

from PIL import Image

OUT = Path(r"C:/Users/Admin/ComfyUI/output")


def params(p: Path):
    g = json.loads(Image.open(p).info.get("prompt", "{}"))
    ks = strength = None
    for n in g.values():
        ct = n.get("class_type", "")
        if ct == "KSampler":
            ks = n["inputs"]
        if ct == "LoraLoaderModelOnly" and "union" in (n["inputs"].get("lora_name") or ""):
            strength = n["inputs"].get("strength_model")
    if not ks:
        return None
    return {"strength": strength, "steps": ks.get("steps"), "cfg": ks.get("cfg"),
            "seed": str(ks.get("seed")), "denoise": ks.get("denoise")}


if __name__ == "__main__":
    print(f"{'file':22} {'str':4} {'stp':4} {'cfg':4} {'dn':4} {'seed'}")
    print("-" * 60)
    seen = set()
    combos = {}
    for f in sorted(OUT.glob("qie_base_*.png")):
        p = params(f)
        if not p:
            continue
        print(f"{f.name:22} {p['strength']!s:4} {p['steps']!s:4} {p['cfg']!s:4} {p['denoise']!s:4} {p['seed']}")
        key = (p["strength"], p["steps"], p["cfg"])
        combos[key] = combos.get(key, 0) + 1
    print("\n=== distinct (strength, steps, cfg) combos in combined qie_base ===")
    for k, c in sorted(combos.items(), key=lambda x: str(x[0])):
        flag = "  <-- == standalone-good" if k == (1.0, 20, 4.0) else ""
        print(f"  {k}  x{c}{flag}")
    print(f"\nstandalone-good config (1.0, 20, 4.0) present in combined sweep: "
          f"{(1.0, 20, 4.0) in combos}")
