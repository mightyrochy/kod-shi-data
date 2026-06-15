"""Workflow template utilities."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

_WORKFLOWS_DIR = Path(__file__).parent

# Placeholder keys and their expected Python types for type-safe filling.
_PLACEHOLDER_TYPES: dict[str, type] = {
    "__PERSON_IMAGE__": str,
    "__REF_IMAGE__": str,
    "__POSITIVE_PROMPT__": str,
    "__NEGATIVE_PROMPT__": str,
    "__OUTPUT_PREFIX__": str,
    "__SEED__": int,
    "__STEPS__": int,
    "__WIDTH__": int,
    "__HEIGHT__": int,
    "__CFG__": float,
    "__SAMPLER__": str,
    "__SCHEDULER__": str,
}

# A string that still looks like an unfilled placeholder after a fill is a bug:
# it means the template carried a token the caller never supplied a value for.
_PLACEHOLDER_RE = re.compile(r"^__[A-Z][A-Z0-9_]*__$")


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

    Raises KeyError if a known placeholder in the template has no entry in params,
    and ValueError (fail-loud) if any placeholder-shaped string survives the fill —
    e.g. a typo'd token the filler does not recognise.
    """
    filled = copy.deepcopy(template)
    _walk(filled, params)
    _assert_filled(filled)
    return filled


def _assert_filled(node, path: str = "$") -> None:
    """Raise if any ``__PLACEHOLDER__``-shaped string remains in the filled tree."""
    if isinstance(node, dict):
        for key, val in node.items():
            _assert_filled(val, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _assert_filled(item, f"{path}[{index}]")
    elif isinstance(node, str) and _PLACEHOLDER_RE.match(node):
        raise ValueError(f"Unfilled placeholder {node!r} remains at {path}")


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
