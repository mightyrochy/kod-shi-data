"""Phase 0 engine capability verifier.

This script is intentionally read-only. It queries ComfyUI /object_info and
checks whether candidate engines expose the three required channels:

1. garment/reference image conditioning;
2. masked edit / inpaint;
3. body/pose control.

It does not submit prompts and never runs generation.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from typing import Any

import requests


DEFAULT_COMFYUI_URL = "http://127.0.0.1:8000"


@dataclass
class Check:
    name: str
    passed: bool
    evidence: str


@dataclass
class EngineReport:
    engine: str
    passed: bool
    checks: list[Check]
    notes: list[str]


def _node(info: dict[str, Any], name: str) -> dict[str, Any] | None:
    node = info.get(name)
    return node if isinstance(node, dict) else None


def _node_present(info: dict[str, Any], name: str) -> bool:
    return _node(info, name) is not None


def _api_node(info: dict[str, Any], name: str) -> bool:
    node = _node(info, name)
    return bool(node and node.get("api_node") is True)


def _input_names(info: dict[str, Any], node_name: str, group: str) -> set[str]:
    node = _node(info, node_name)
    if not node:
        return set()
    inputs = node.get("input", {}).get(group, {})
    return set(inputs) if isinstance(inputs, dict) else set()


def _has_optional_input(info: dict[str, Any], node_name: str, input_name: str) -> bool:
    return input_name in _input_names(info, node_name, "optional")


def _has_required_input(info: dict[str, Any], node_name: str, input_name: str) -> bool:
    return input_name in _input_names(info, node_name, "required")


def _combo_options(info: dict[str, Any], node_name: str, input_name: str) -> list[str]:
    node = _node(info, node_name)
    if not node:
        return []
    for group in ("required", "optional"):
        inputs = node.get("input", {}).get(group, {})
        if not isinstance(inputs, dict) or input_name not in inputs:
            continue
        value = inputs[input_name]
        if (
            isinstance(value, list)
            and value
            and isinstance(value[0], list)
        ):
            return [str(item) for item in value[0]]
        if (
            isinstance(value, list)
            and len(value) > 1
            and isinstance(value[1], dict)
            and isinstance(value[1].get("options"), list)
        ):
            return [str(item) for item in value[1]["options"]]
    return []


def _has_option_containing(
    info: dict[str, Any], node_name: str, input_name: str, needle: str
) -> bool:
    needle = needle.lower()
    return any(needle in option.lower() for option in _combo_options(info, node_name, input_name))


def _present_check(info: dict[str, Any], name: str, node_name: str) -> Check:
    return Check(
        name=name,
        passed=_node_present(info, node_name),
        evidence=f"node {node_name} {'present' if _node_present(info, node_name) else 'missing'}",
    )


def evaluate_qwen_edit(info: dict[str, Any]) -> EngineReport:
    checks: list[Check] = []

    qwen_weights = [
        option
        for option in _combo_options(info, "UNETLoader", "unet_name")
        if "qwen_image_edit_2511" in option.lower()
    ]
    checks.append(Check(
        "local_qwen_edit_weights",
        bool(qwen_weights),
        f"UNETLoader.unet_name contains: {', '.join(qwen_weights) or 'none'}",
    ))

    image_inputs = [
        name for name in ("image1", "image2", "image3")
        if _has_optional_input(info, "TextEncodeQwenImageEditPlus", name)
    ]
    checks.append(Check(
        "garment_image_conditioning",
        bool(image_inputs),
        f"TextEncodeQwenImageEditPlus optional image inputs: {', '.join(image_inputs) or 'none'}",
    ))

    patch_options = _combo_options(info, "ModelPatchLoader", "name")
    checks.append(Check(
        "control_model_patch_weights",
        bool(patch_options),
        f"ModelPatchLoader.name options: {len(patch_options)}",
    ))

    qwen_cn_mask = (
        _node_present(info, "QwenImageDiffsynthControlnet")
        and _has_required_input(info, "QwenImageDiffsynthControlnet", "image")
        and _has_optional_input(info, "QwenImageDiffsynthControlnet", "mask")
    )
    checks.append(Check(
        "masked_body_control_node",
        qwen_cn_mask,
        "QwenImageDiffsynthControlnet requires image and has optional mask"
        if qwen_cn_mask else "QwenImageDiffsynthControlnet mask/control signature missing",
    ))

    notes = [
        "Qwen currently has multi-image edit conditioning.",
        "It does not pass Phase 0 until a usable MODEL_PATCH weight is present and a graph proves image+mask+control can be combined.",
    ]
    return EngineReport(
        engine="qwen_image_edit_2511_local",
        passed=all(check.passed for check in checks),
        checks=checks,
        notes=notes,
    )


def evaluate_flux_local(info: dict[str, Any]) -> EngineReport:
    checks: list[Check] = []

    checks.append(Check(
        "local_flux_fill_weights",
        _has_option_containing(info, "UNETLoader", "unet_name", "flux1-fill"),
        "UNETLoader.unet_name contains flux1-fill"
        if _has_option_containing(info, "UNETLoader", "unet_name", "flux1-fill")
        else "UNETLoader.unet_name has no flux1-fill model",
    ))

    inpaint_primitives = (
        _node_present(info, "InpaintModelConditioning")
        and _node_present(info, "VAEEncodeForInpaint")
        and _node_present(info, "ConditioningSetMask")
    )
    checks.append(Check(
        "masked_edit_primitives",
        inpaint_primitives,
        "InpaintModelConditioning + VAEEncodeForInpaint + ConditioningSetMask present"
        if inpaint_primitives else "one or more inpaint/mask primitives missing",
    ))

    controlnet_options = _combo_options(info, "ControlNetLoader", "control_net_name")
    pose_preprocessors = [
        name for name in ("OpenposePreprocessor", "DensePosePreprocessor", "DepthAnythingV2Preprocessor")
        if _node_present(info, name)
    ]
    checks.append(Check(
        "body_pose_control_weights",
        bool(controlnet_options) and bool(pose_preprocessors),
        f"ControlNet models: {len(controlnet_options)}; pose/depth preprocessors: {', '.join(pose_preprocessors) or 'none'}",
    ))

    clipvision_options = _combo_options(info, "CLIPVisionLoader", "clip_name")
    local_reference_nodes = [
        name for name in (
            "CLIPVisionEncode",
            "CLIPVisionLoader",
            "ImpactIPAdapterApplySEGS",
            "FluxKontextMultiReferenceLatentMethod",
        )
        if _node_present(info, name)
    ]
    checks.append(Check(
        "garment_image_adapter_stack",
        bool(clipvision_options),
        f"reference-related nodes: {', '.join(local_reference_nodes) or 'none'}; CLIPVision models: {len(clipvision_options)}",
    ))

    notes = [
        "Local FLUX has the strongest local masked-edit foundation because flux1-fill-dev is installed.",
        "It does not pass Phase 0 until local ControlNet weights and a real garment image adapter/vision stack are installed and visible in /object_info.",
    ]
    return EngineReport(
        engine="flux_fill_local",
        passed=all(check.passed for check in checks),
        checks=checks,
        notes=notes,
    )


def evaluate_bfl_api(info: dict[str, Any]) -> EngineReport:
    checks = [
        Check(
            "api_vto_garment_conditioning",
            _api_node(info, "FluxVTONode")
            and _has_required_input(info, "FluxVTONode", "person")
            and _has_required_input(info, "FluxVTONode", "garment"),
            "FluxVTONode is a BFL API node with person+garment inputs",
        ),
        Check(
            "api_fill_masked_edit",
            _api_node(info, "FluxProFillNode")
            and _has_required_input(info, "FluxProFillNode", "image")
            and _has_required_input(info, "FluxProFillNode", "mask"),
            "FluxProFillNode is a BFL API node with image+mask inputs",
        ),
        Check(
            "api_body_pose_control",
            False,
            "no BFL API node in current /object_info exposes pose/body control input",
        ),
    ]
    return EngineReport(
        engine="bfl_partner_api_flux",
        passed=False,
        checks=checks,
        notes=[
            "These nodes are paid/partner API nodes, not local open-source inference.",
            "They can inform capability research but do not satisfy the local-open product constraint.",
        ],
    )


def fetch_object_info(base_url: str) -> dict[str, Any]:
    resp = requests.get(f"{base_url.rstrip('/')}/object_info", timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise TypeError("/object_info returned non-object JSON")
    return data


def render_text(reports: list[EngineReport], node_count: int) -> str:
    lines = [
        f"ComfyUI object_info node count: {node_count}",
        "",
    ]
    for report in reports:
        status = "PASS" if report.passed else "FAIL"
        lines.append(f"## {report.engine}: {status}")
        for check in report.checks:
            check_status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {check_status} {check.name}: {check.evidence}")
        for note in report.notes:
            lines.append(f"  note: {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfyui", default=DEFAULT_COMFYUI_URL)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args()

    info = fetch_object_info(args.comfyui)
    reports = [
        evaluate_qwen_edit(info),
        evaluate_flux_local(info),
        evaluate_bfl_api(info),
    ]

    if args.json:
        print(json.dumps({
            "comfyui": args.comfyui,
            "node_count": len(info),
            "reports": [asdict(report) for report in reports],
        }, indent=2, ensure_ascii=False))
    else:
        print(render_text(reports, len(info)))
    return 0 if any(report.passed for report in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
