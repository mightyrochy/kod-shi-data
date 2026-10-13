"""E-016 — diff the embedded QIE execution graph between a known-good standalone PNG and a
combined-workflow qie_base PNG. No generation. Answers: what does the combined graph change about
the QIE computation (KSampler config / latent source / sampling chain / LoRA / model)?"""
import json
import sys
from pathlib import Path

from PIL import Image

OUT = Path(r"C:/Users/Admin/ComfyUI/output")
RES = Path(__file__).resolve().parent / "results"

STANDALONE = RES / "qie_pose.png"
COMBINED = OUT / "qie_base_00023_.png"

# class_types that define the QIE computation we care about
CARE = {
    "KSampler", "KSamplerAdvanced",
    "ModelSamplingAuraFlow", "CFGNorm", "CFGZeroStar",
    "LoraLoaderModelOnly", "LoraLoader",
    "UNETLoader", "VAELoader", "CLIPLoader",
    "VAEEncode", "EmptyLatentImage", "EmptySD3LatentImage",
    "TextEncodeQwenImageEditPlus",
    "FluxKontextImageScale", "FluxKontextMultiReferenceLatentMethod",
    "ReferenceLatent",
}


def load_graph(p: Path):
    info = Image.open(p).info
    g = info.get("prompt")
    if not g:
        print(f"!! no embedded prompt graph in {p.name}")
        return {}
    return json.loads(g)


def node_index(g):
    """class_type -> list of (node_id, inputs) sorted by id"""
    idx = {}
    for nid, n in g.items():
        ct = n.get("class_type", "")
        idx.setdefault(ct, []).append((nid, n.get("inputs", {})))
    for ct in idx:
        idx[ct].sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
    return idx


def fmt_inputs(inp):
    out = {}
    for k, v in inp.items():
        # links are [node_id, slot] lists; keep scalar params as-is
        if isinstance(v, list) and len(v) == 2 and isinstance(v[1], int):
            out[k] = f"<link {v[0]}:{v[1]}>"
        else:
            out[k] = v
    return out


def main():
    ga = load_graph(STANDALONE)
    gb = load_graph(COMBINED)
    if not ga or not gb:
        return
    ia, ib = node_index(ga), node_index(gb)
    print(f"STANDALONE = {STANDALONE.name}   ({len(ga)} nodes)")
    print(f"COMBINED   = {COMBINED.name}   ({len(gb)} nodes)\n")

    for ct in sorted(CARE):
        a = ia.get(ct, [])
        b = ib.get(ct, [])
        if not a and not b:
            continue
        print(f"=== {ct}  (standalone:{len(a)}  combined:{len(b)}) ===")
        for tag, lst in (("S", a), ("C", b)):
            for nid, inp in lst:
                print(f"  [{tag} #{nid}] {json.dumps(fmt_inputs(inp), ensure_ascii=False)}")
        print()


if __name__ == "__main__":
    main()
