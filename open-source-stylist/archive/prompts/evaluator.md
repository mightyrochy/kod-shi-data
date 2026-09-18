# Evaluation Prompt

Compare the generated image against:

- source person image;
- garment references;
- outfit_layout;
- qwen_prompt.

Return JSON with:

- identity_preserved: pass/fail
- face_preserved: pass/fail
- body_shape_preserved: pass/fail
- item_presence: list of each item with pass/fail
- layering_rules: list of each rule with pass/fail
- detail_preservation: pass/fail
- unwanted_changes: list
- overall_score: number from 0 to 1
- retry_instruction: concise instruction for the next generation attempt

Rules:

- Be strict.
- Fail if a required item is missing or simplified beyond recognition.
- Fail if the outfit logic is not followed.
- Do not approve a beautiful image that violates the outfit layout.

