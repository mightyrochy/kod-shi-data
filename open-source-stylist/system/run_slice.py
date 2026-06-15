"""Minimal reproducible vertical slice — one honest run, no repair, no VLM.

This is the seed of the orchestrator that BUILD_PLAN names but the tree lacks.
Its only job is to prove the chain
    validated inputs -> exact generation request -> exact filled workflow
    -> output + hashes -> segmentation + sanity -> limited honest gates
    -> owner checkpoint -> run manifest
runs once, reproducibly, with every request parameter actually reaching the engine.

It deliberately does NOT: route repairs, call a VLM, restore background, colour-match,
or self-declare a quality verdict. The owner reviews `generated.png` at the checkpoint.

Two modes:
    --no-generate (default)  build the request + the exact filled workflow + an input
                             manifest, without touching ComfyUI. Proves reproducibility
                             and that cfg/sampler/scheduler/negative thread through.
    --generate               additionally run the engine, segment, sanity-check, and
                             measure the limited gates, then write the full manifest.

Run:
    python -m system.run_slice --outfit assets/outfits/outfit_001/outfit_package.json \
        --person assets/person/person_front.png --board hybrid_mask_crop --seed 42
    # add --generate to actually call ComfyUI (the owner-checkpoint path)
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from system.adapter.adapter import build_generation_request
from system.adapter.panel import file_sha256, resolve_board
from system.workflows import fill_workflow, load_template

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"

# Engine -> workflow template. The request's `engine` field selects the template;
# nothing else is hard-coded, so cfg/steps/sampler now come from the request.
ENGINE_WORKFLOW = {
    "qie-2511-lightning": "qie2511_vton_lightning",
    "qie-2511": "qie2511_vton",
}

# Gate thresholds — only the static-photo calibrations that survive the 2026-06-13
# erratum (see CURRENT_STATE.md). These are limited instruments, not a product verdict.
COLOR_PASS = 3.0
COLOR_FAIL = 5.0
IDENTITY_THRESHOLD = 0.57
PROPORTIONS_THRESHOLD = 5.3

GATE_CAVEATS = {
    "identity": "ArcFace cosine — FACE ONLY. Says nothing about hair, skin, body, pose, background.",
    "proportions": "Clothed-silhouette row widths — diagnostic, NOT a body-distortion verdict; volume garments and framing move the number. See framing_delta_pct.",
    "color": "Mean CIEDE2000 with normalize_l=True — a HUE/CHROMA indicator, blind to absolute lightness; does not verify 'same garment'.",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _select_template(engine: str) -> str:
    if engine not in ENGINE_WORKFLOW:
        raise ValueError(
            f"No workflow mapped for engine {engine!r}; known: {', '.join(sorted(ENGINE_WORKFLOW))}"
        )
    return ENGINE_WORKFLOW[engine]


def _fill(template: dict, request: dict, person_ref: str, board_ref: str) -> dict:
    """Fill a template from a request. Every KSampler/prompt param comes from here."""
    params = request["params"]
    return fill_workflow(template, {
        "__PERSON_IMAGE__": person_ref,
        "__REF_IMAGE__": board_ref,
        "__POSITIVE_PROMPT__": request["prompt"],
        "__NEGATIVE_PROMPT__": request["negative_prompt"],
        "__CFG__": params["cfg"],
        "__SAMPLER__": params["sampler"],
        "__SCHEDULER__": params["scheduler"],
        "__SEED__": params["seed"],
        "__STEPS__": params["steps"],
        "__WIDTH__": params["width"],
        "__HEIGHT__": params["height"],
        "__OUTPUT_PREFIX__": request["request_id"],
    })


def _load_references(references_path: Path | None) -> dict:
    """Optional region -> (ref_image, ref_mask) map for the colour gate.

    JSON form: {"top": ["path/to/blouse.webp", "path/to/blouse_mask.png"], ...}.
    Absent -> colour gate is skipped with an explicit status, identity/proportions
    still run.
    """
    if references_path is None:
        return {}
    raw = json.loads(references_path.read_text(encoding="utf-8"))
    out = {}
    for region, pair in raw.items():
        image, mask = pair
        out[region] = (str((ROOT / image).resolve()), str((ROOT / mask).resolve()))
    return out


def _color_verdict(value):
    if value is None:
        return "INVALID"
    if value <= COLOR_PASS:
        return "PASS"
    if value <= COLOR_FAIL:
        return "WARN"
    return "FAIL"


def _flags_to_json(sanity: dict) -> dict:
    return {
        region: [{"check": flag.check, "detail": flag.detail} for flag in result.flags]
        for region, result in sanity.items()
        if not result.clean
    }


def _measure(generated: Path, run_dir: Path, person_image: Path,
             person_mask: Path | None, references: dict) -> dict:
    """Segmentation + sanity + the limited honest gates. Imports the heavy deps
    lazily so --no-generate never loads segmentation / insightface."""
    from system.clients.comfyui import ComfyUIClient
    from system.gates import body_pose
    from system.gates.color import compare_regions
    from system.gates.identity import compare_faces
    from system.gates.proportions import compare as compare_proportions
    from system.segmentation.grounded_sam import segment
    from system.segmentation.prompts import generated_prompts
    from system.segmentation.sanity import check_all

    regions = ["person", "face", *references.keys()]
    client = ComfyUIClient()
    masks = segment(generated, generated_prompts(*regions), client, run_dir / "masks")
    sanity = check_all(masks)
    flags = _flags_to_json(sanity)

    result = {"sanity_flags": flags, "gate_caveats": GATE_CAVEATS, "color": {}}

    for region, (ref_image, ref_mask) in references.items():
        if region in flags:
            result["color"][region] = {"verdict": "SKIP_SANITY", "flags": flags[region]}
            continue
        if region not in masks:
            result["color"][region] = {"verdict": "NO_OUTPUT_MASK"}
            continue
        measurement = compare_regions(generated, masks[region], ref_image, ref_mask)
        result["color"][region] = {**measurement, "verdict": _color_verdict(measurement["delta_e_mean"])}

    identity = compare_faces(generated, person_image)
    cosine = identity["cosine"]
    result["identity"] = {
        **identity,
        "verdict": ("SKIP_DETECTION" if cosine is None
                    else "PASS" if cosine >= IDENTITY_THRESHOLD else "FAIL"),
    }

    if person_mask is None:
        result["proportions"] = {"verdict": "NO_PERSON_MASK",
                                 "note": "pass --person-mask to enable the diagnostic"}
    elif "person" in flags or "person" not in masks:
        result["proportions"] = {"verdict": "SKIP_SANITY", "flags": flags.get("person", [])}
    else:
        proportions = compare_proportions(person_mask, masks["person"])
        score = proportions["max_abs_change_pct"]
        result["proportions"] = {
            **proportions,
            "verdict": ("SKIP_MEASUREMENT" if score is None
                        else "PASS" if score <= PROPORTIONS_THRESHOLD else "FAIL"),
        }

    # Skeletal body-shape (clothing-robust) — the honest body check that the
    # clothed-silhouette proportions gate above cannot give.
    result["body"] = body_pose.compare(person_image, generated)
    return result


def run_slice(args: argparse.Namespace) -> Path:
    outfit_path = (ROOT / args.outfit).resolve() if not Path(args.outfit).is_absolute() else Path(args.outfit)
    person_path = (ROOT / args.person).resolve() if not Path(args.person).is_absolute() else Path(args.person)
    for label, path in (("outfit package", outfit_path), ("person image", person_path)):
        if not path.is_file():
            raise FileNotFoundError(f"Missing {label}: {path}")

    package = json.loads(outfit_path.read_text(encoding="utf-8"))
    resolution = (args.width, args.height) if args.width and args.height else None

    request = build_generation_request(
        package, person_path, reference_board_variant=args.board,
        seed=args.seed, steps=args.steps, resolution=resolution,
        engine=args.engine, cfg=args.cfg,
    )

    board_path = resolve_board(package, args.board)            # verifies frozen SHA-256
    template_name = _select_template(args.engine)
    template = load_template(template_name)
    layout_path = (ROOT / package["layout_path"]).resolve()

    run_id = f"{package['outfit_id']}_{args.board}_s{args.seed}_{request['request_id']}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "run_id": run_id,
        "created_utc": _now(),
        "mode": "generate" if args.generate else "dry-run",
        "inputs": {
            "outfit_package": {"path": str(outfit_path), "sha256": file_sha256(outfit_path)},
            "person_image": {"path": str(person_path), "sha256": file_sha256(person_path)},
            "reference_board": {"variant": args.board, "path": str(board_path),
                                "sha256": file_sha256(board_path)},
            "layout": {"path": str(layout_path), "sha256": file_sha256(layout_path)},
            "workflow_template": {"name": template_name,
                                  "path": str(ROOT / "system/workflows" / f"{template_name}.json"),
                                  "sha256": file_sha256(ROOT / "system/workflows" / f"{template_name}.json")},
        },
        "request": request,
        "gate_thresholds": {"color_pass": COLOR_PASS, "color_fail": COLOR_FAIL,
                            "identity": IDENTITY_THRESHOLD, "proportions": PROPORTIONS_THRESHOLD},
    }

    if not args.generate:
        # Dry run: produce the exact filled workflow with LOCAL image names so the
        # artifact is complete and every parameter is visibly threaded through.
        filled = _fill(template, request, person_path.name, board_path.name)
        filled_path = run_dir / "filled_workflow.dryrun.json"
        _write_json(filled_path, filled)
        manifest["filled_workflow"] = {
            "path": str(filled_path), "sha256": file_sha256(filled_path),
            "note": "DRY RUN — __PERSON_IMAGE__/__REF_IMAGE__ are local filenames, not uploaded ComfyUI names.",
        }
        _write_json(run_dir / "manifest.json", manifest)
        _write_report(run_dir, manifest)
        return run_dir

    # --- generate path (owner checkpoint) ---
    from system.clients.comfyui import ComfyUIClient
    client = ComfyUIClient()
    person_ref = client.upload_image(person_path)
    board_ref = client.upload_image(board_path)
    filled = _fill(template, request, person_ref, board_ref)
    filled_path = run_dir / "filled_workflow.json"
    _write_json(filled_path, filled)

    started = time.monotonic()
    prompt_id = client.submit(filled)
    outputs = client.poll(prompt_id, timeout=args.timeout)
    output_path = run_dir / "generated.png"
    _download_first(client, outputs, request["request_id"], output_path)
    elapsed = round(time.monotonic() - started, 2)
    client.free()

    manifest["filled_workflow"] = {"path": str(filled_path), "sha256": file_sha256(filled_path)}
    manifest["generation"] = {
        "comfyui_prompt_id": prompt_id, "seconds": elapsed,
        "uploaded": {"person": person_ref, "board": board_ref},
        "output": {"path": str(output_path), "sha256": file_sha256(output_path)},
    }

    person_mask = None
    if args.person_mask:
        person_mask = (ROOT / args.person_mask).resolve() if not Path(args.person_mask).is_absolute() else Path(args.person_mask)
        if not person_mask.is_file():
            raise FileNotFoundError(f"Missing --person-mask: {person_mask}")
    references = _load_references(
        (ROOT / args.references).resolve() if args.references and not Path(args.references).is_absolute()
        else (Path(args.references) if args.references else None)
    )
    manifest["measurement"] = _measure(output_path, run_dir, person_path, person_mask, references)

    _write_json(run_dir / "manifest.json", manifest)
    _write_report(run_dir, manifest)
    return run_dir


def _download_first(client, outputs: dict, prefix: str, destination: Path) -> None:
    for node_output in outputs.values():
        for image_info in node_output.get("images", []):
            if image_info.get("filename", "").startswith(prefix):
                data = client.download(image_info["filename"],
                                       image_info.get("subfolder", ""),
                                       image_info.get("type", "output"))
                destination.write_bytes(data)
                return
    raise RuntimeError(f"ComfyUI produced no image with prefix {prefix!r}")


def _write_report(run_dir: Path, manifest: dict) -> None:
    lines = [
        f"# Run {manifest['run_id']}",
        "",
        f"- mode: **{manifest['mode']}**  ·  created: {manifest['created_utc']}",
        f"- engine: `{manifest['request']['engine']}`  ·  params: `{json.dumps(manifest['request']['params'])}`",
        f"- board: `{manifest['inputs']['reference_board']['variant']}` "
        f"(sha256 {manifest['inputs']['reference_board']['sha256'][:12]}…)",
        "",
    ]
    if manifest["mode"] == "dry-run":
        lines += [
            "**Dry run** — no generation. The exact filled workflow is saved; every "
            "request parameter (cfg/sampler/scheduler/negative/seed/steps/size) is "
            "threaded into it. Re-run with `--generate` for the owner checkpoint.",
        ]
        run_dir_report = run_dir / "report.md"
        run_dir_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    m = manifest.get("measurement", {})
    ident = m.get("identity", {})
    prop = m.get("proportions", {})
    lines += [
        f"- output: `generated.png` (sha256 {manifest['generation']['output']['sha256'][:12]}…), "
        f"{manifest['generation']['seconds']}s",
        "",
        "## Gates (limited instruments — not a product verdict)",
        f"- identity (face only): cosine={ident.get('cosine')} → **{ident.get('verdict')}**",
        f"- proportions (clothed silhouette — diagnostic): max_abs={prop.get('max_abs_change_pct')} "
        f"framing_delta={prop.get('framing_delta_pct')} → **{prop.get('verdict')}**",
    ]
    body = m.get("body", {})
    if body.get("verdict") == "MEASURED":
        ch = body["change_pct"]
        lines.append(
            f"- body (pose joints — clothing-robust): hipΔ={ch['hip_width_norm']}%  "
            f"shoulderΔ={ch['shoulder_width_norm']}%  ratioΔ={ch['shoulder_hip_ratio']}%  "
            f"(pose match {body['pose_mismatch_deg']}°, vis {body['min_visibility']})"
        )
    elif body:
        lines.append(f"- body (pose joints): {body.get('verdict')}")
    for region, c in m.get("color", {}).items():
        if "delta_e_mean" not in c:
            lines.append(f"- color[{region}]: {c.get('verdict')}")
            continue
        rel = "" if c.get("hue_reliable") else "  ⚠hue unreliable (low chroma)"
        lines.append(
            f"- color[{region}]: dE={c.get('delta_e_mean')} → **{c.get('verdict')}**  ·  "
            f"hueΔ={c.get('hue_delta_deg')}°  chromaΔ={c.get('chroma_delta')}  Lshift={c.get('l_shift')}{rel}"
        )
    if m.get("sanity_flags"):
        lines += ["", f"⚠ sanity flags: {list(m['sanity_flags'])}"]
    lines += [
        "",
        "## Owner checkpoint",
        "Review `generated.png` against the four criteria (identity, all items present, "
        "layering, colour/texture). The gates above are advisory only.",
    ]
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Minimal reproducible vertical slice")
    parser.add_argument("--outfit", required=True, help="path to outfit_package.json")
    parser.add_argument("--person", required=True, help="path to person image")
    parser.add_argument("--board", required=True, help="reference board variant name")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--engine", default="qie-2511-lightning", choices=sorted(ENGINE_WORKFLOW))
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--cfg", type=float, default=1.0)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--person-mask", default=None, help="person silhouette mask for the proportions gate")
    parser.add_argument("--references", default=None, help="JSON region -> [ref_image, ref_mask] for the colour gate")
    parser.add_argument("--generate", action="store_true", help="actually call ComfyUI (owner-checkpoint path)")
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args()

    run_dir = run_slice(args)
    rel = run_dir.relative_to(ROOT)
    if args.generate:
        print(f"\nRun complete. Review: {rel / 'generated.png'}")
        print(f"Manifest: {rel / 'manifest.json'}  ·  Report: {rel / 'report.md'}")
        print("Owner checkpoint: judge generated.png against the four criteria before any next stage.")
    else:
        print(f"\nDry run complete (no generation). {rel}")
        print(f"Filled workflow: {rel / 'filled_workflow.dryrun.json'}  ·  Manifest: {rel / 'manifest.json'}")
        print("Re-run with --generate to produce an image (needs ComfyUI live).")


if __name__ == "__main__":
    main()
