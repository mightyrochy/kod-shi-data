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
