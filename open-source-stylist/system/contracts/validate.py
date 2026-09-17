#!/usr/bin/env python3
"""
Validate all sample instances against their schemas.

Run from the project root:
    python system/contracts/validate.py

Requires: pip install jsonschema
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

CONTRACTS_DIR = Path(__file__).parent
SAMPLES_DIR = CONTRACTS_DIR / "samples"

SCHEMAS = [
    "person_profile",
    "outfit_package",
    "generation_request",
    "generation_result",
    "region_map",
    "evaluation_verdict",
    "repair_plan",
    "final_output",
]

PROJECT_ROOT = CONTRACTS_DIR.parent.parent
ACTIVE_OUTFIT_PACKAGE = PROJECT_ROOT / "assets/outfits/outfit_001/outfit_package.json"
ACTIVE_PERSON_IMAGE = PROJECT_ROOT / "assets/person/person_front.png"
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    results = []

    for name in SCHEMAS:
        schema_path = CONTRACTS_DIR / f"{name}.json"
        sample_path = SAMPLES_DIR / f"{name}_sample.json"

        if not schema_path.exists():
            results.append((name, "MISSING_SCHEMA", ""))
            continue
        if not sample_path.exists():
            results.append((name, "MISSING_SAMPLE", ""))
            continue

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        sample = json.loads(sample_path.read_text(encoding="utf-8"))

        try:
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(sample)
            results.append((name, "PASS", ""))
        except jsonschema.ValidationError as e:
            results.append((name, "FAIL", e.message))
        except jsonschema.SchemaError as e:
            results.append((name, "SCHEMA_ERROR", e.message))

    outfit_schema = json.loads((CONTRACTS_DIR / "outfit_package.json").read_text(encoding="utf-8"))
    active_outfit = json.loads(ACTIVE_OUTFIT_PACKAGE.read_text(encoding="utf-8"))
    try:
        Draft202012Validator(outfit_schema).validate(active_outfit)
        missing = []
        for item in active_outfit["items"]:
            for ref_path in item["reference_image_paths"]:
                if not (PROJECT_ROOT / ref_path).is_file():
                    missing.append(ref_path)
        if not (PROJECT_ROOT / active_outfit["layout_path"]).is_file():
            missing.append(active_outfit["layout_path"])
        if missing:
            results.append(("active_outfit_package", "FAIL", f"missing paths: {missing}"))
        else:
            from system.adapter.adapter import build_generation_request
            from system.adapter.panel import resolve_board
            from system.adapter.prompt import build_prompt

            for variant in active_outfit["reference_board"]["variants"]:
                resolve_board(active_outfit, variant, PROJECT_ROOT)
            build_prompt(active_outfit, PROJECT_ROOT)
            results.append(("active_outfit_package", "PASS", ""))

            try:
                request_schema = json.loads(
                    (CONTRACTS_DIR / "generation_request.json").read_text(encoding="utf-8")
                )
                for variant in active_outfit["reference_board"]["variants"]:
                    request = build_generation_request(
                        active_outfit,
                        ACTIVE_PERSON_IMAGE,
                        reference_board_variant=variant,
                        seed=42,
                        resolution=(720, 1024),
                    )
                    Draft202012Validator(request_schema).validate(request)
                results.append(("active_generation_requests", "PASS", ""))
            except jsonschema.ValidationError as e:
                results.append(("active_generation_requests", "FAIL", e.message))
            except (FileNotFoundError, RuntimeError, ValueError) as e:
                results.append(("active_generation_requests", "FAIL", str(e)))
    except jsonschema.ValidationError as e:
        results.append(("active_outfit_package", "FAIL", e.message))
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        results.append(("active_outfit_package", "FAIL", str(e)))

    width = max(len(name) for name, _, _ in results) + 2
    print("\n=== contracts/validate.py ===\n")
    for name, status, msg in results:
        line = f"  {name:<{width}} {status}"
        if msg:
            short = msg[:100] + ("..." if len(msg) > 100 else "")
            line += f"  — {short}"
        print(line)

    passed = sum(1 for _, s, _ in results if s == "PASS")
    total = len(results)
    print(f"\n  {passed}/{total} passed\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
