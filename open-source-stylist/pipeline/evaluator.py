"""Outfit transfer evaluator using a local VLM (Qwen3-VL-8B via LM Studio).

Four evaluation criteria (from CLAUDE.md):
  1. Identity preserved — same person, face, hair, body shape
  2. All outfit items present — every item from the outfit package is visible
  3. Outfit logic followed — layering, visibility order, what's over what
  4. Color and texture match — reference image accuracy per item

A result passes only when all four criteria pass, or the user explicitly accepts.
"""

from pathlib import Path

from pipeline.lmstudio_client import LMStudioClient

DEFAULT_VLM_MODEL = "qwen3-vl-8b-instruct"

EVAL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "identity_preserved": {"type": "boolean"},
        "identity_notes": {"type": "string"},
        "outfit_items_present": {"type": "boolean"},
        "items_notes": {"type": "string"},
        "outfit_logic_followed": {"type": "boolean"},
        "logic_notes": {"type": "string"},
        "colors_textures_match": {"type": "boolean"},
        "color_notes": {"type": "string"},
        "overall_pass": {"type": "boolean"},
        "summary": {"type": "string"},
    },
    "required": [
        "identity_preserved",
        "identity_notes",
        "outfit_items_present",
        "items_notes",
        "outfit_logic_followed",
        "logic_notes",
        "colors_textures_match",
        "color_notes",
        "overall_pass",
        "summary",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a fashion QA evaluator. You receive images and evaluate "
    "whether an AI-generated outfit transfer meets specific criteria. "
    "Answer strictly based on what you see in the images. "
    "Do not speculate. If you cannot see a detail clearly, note that uncertainty."
)


def _build_eval_prompt(outfit_package: dict) -> str:
    items = outfit_package.get("items", [])
    logic = outfit_package.get("outfit_logic", [])
    negatives = outfit_package.get("negative_constraints", [])

    item_list = "\n".join(
        f"  - {it.get('name', '?')}: {it.get('visual_description', '')} "
        f"(must_preserve: {', '.join(it.get('must_preserve', [])[:3])})"
        for it in sorted(items, key=lambda x: x.get("visibility_priority", 0), reverse=True)
    )

    logic_list = "\n".join(f"  - {r}" for r in logic) if logic else "  (none specified)"
    neg_list = "\n".join(f"  - {n}" for n in negatives[:6]) if negatives else "  (none)"

    return f"""You are evaluating an AI outfit transfer.

Image 1 is the ORIGINAL person photo (before).
Image 2 is the GENERATED result (after).

EXPECTED OUTFIT ITEMS:
{item_list}

OUTFIT LOGIC (layering / visibility rules):
{logic_list}

NEGATIVE CONSTRAINTS (must not happen):
{neg_list}

Evaluate the generated image (image 2) against these four criteria:

1. IDENTITY: Is the same person visible — same face, same hair, same body shape, same pose, same background? (true/false + notes)

2. ITEMS PRESENT: Are ALL expected outfit items visible in the generated image? List any missing items in notes. (true/false + notes)

3. OUTFIT LOGIC: Does the generated image follow the layering and visibility rules listed above? (true/false + notes)

4. COLORS & TEXTURES: Do the colors and textures of each visible garment match the descriptions above? (true/false + notes)

OVERALL PASS: true only if all four criteria are true. Set to false if any criterion fails.

Respond with JSON only, no explanation outside the JSON."""


class Evaluator:
    def __init__(self, lms: LMStudioClient, model: str = DEFAULT_VLM_MODEL):
        self.lms = lms
        self.model = model

    def evaluate(
        self,
        person_before: Path,
        generated_output: Path,
        outfit_package: dict,
    ) -> dict:
        """Run the 4-criterion evaluation.

        Args:
            person_before: the original person photo (before generation).
            generated_output: the output image from the generation step.
            outfit_package: the outfit_package dict (with items, outfit_logic, etc.).

        Returns:
            A dict matching EVAL_SCHEMA.  overall_pass=True only if all 4 criteria pass.
        """
        prompt = _build_eval_prompt(outfit_package)
        return self.lms.vision_chat(
            prompt=prompt,
            image_paths=[Path(person_before), Path(generated_output)],
            model=self.model,
            system=SYSTEM_PROMPT,
            json_schema=EVAL_SCHEMA,
            schema_name="outfit_evaluation",
            temperature=0.1,
            max_tokens=1500,
        )
