"""Workflow template utilities."""

from __future__ import annotations

import copy
import json
from pathlib import Path

_WORKFLOWS_DIR = Path(__file__).parent

# Placeholder keys and their expected Python types for type-safe filling.
_PLACEHOLDER_TYPES: dict[str, type] = {
    "__PERSON_IMAGE__": str,
    "__REF_IMAGE__": str,
    "__POSITIVE_PROMPT__": str,
    "__OUTPUT_PREFIX__": str,
    "__SEED__": int,
    "__STEPS__": int,
    "__WIDTH__": int,
    "__HEIGHT__": int,
}


def load_template(name: str) -> dict:
    """Load a workflow template JSON by filename (without .json)."""
    path = _WORKFLOWS_DIR / f"{name}.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def fill_workflow(template: dict, params: dict) -> dict:
    """Replace __PLACEHOLDER__ strings with typed values.

    Walks the entire template tree and substitutes any string value that
    exactly matches a placeholder key.  Integer placeholders must be
    provided as int (or a string that parses to int) — the filled value is
    always the correct JSON type.

    Raises KeyError if a placeholder in the template has no entry in params.
    """
    filled = copy.deepcopy(template)
    _walk(filled, params)
    return filled


def _walk(node, params: dict):
    if isinstance(node, dict):
        for key, val in node.items():
            if isinstance(val, str) and val in _PLACEHOLDER_TYPES:
                expected = _PLACEHOLDER_TYPES[val]
                raw = params[val]
                node[key] = expected(raw)
            else:
                _walk(val, params)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            if isinstance(item, str) and item in _PLACEHOLDER_TYPES:
                expected = _PLACEHOLDER_TYPES[item]
                raw = params[item]
                node[i] = expected(raw)
            else:
                _walk(item, params)
