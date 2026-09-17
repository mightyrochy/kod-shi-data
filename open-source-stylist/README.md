# Open Source Stylist

Local outfit-transfer research project.

Python dependencies are pinned in `requirements.txt` (current runtime: Python 3.10).
On Windows, install them with `powershell -ExecutionPolicy Bypass -File system/setup_python.ps1`;
the final step prevents InsightFace's CPU dependency from replacing ONNX Runtime GPU.

```text
person photo + frozen reference board + outfit layout
-> one controlled generation component
-> measured and owner-reviewed result
```

Stack: Python, ComfyUI, Qwen-Image-Edit-2511, GroundingDINO + SAM1,
ArcFace, RTX 4090 Laptop 16GB.

**Status (2026-06-14):** component-testing stage. E-007 v2's original A/B ended
with no winner. Its hybrid supplement produces buttons and wedge sandals in 5/5
outputs and is the next input candidate, but blouse color and silhouette fidelity
remain unresolved. The project does not claim an automated end-to-end pipeline.

## Where to start

- `CLAUDE.md` — project instructions and SOP
- `design/SYSTEM_DESIGN.md` — canonical architecture (V1/V2/V3)
- `METHODOLOGY.md` — how knowledge is produced and changes accepted
- `BUILD_PLAN.md` — assembly plan: stages 0–7, contracts, acceptance criteria
- `knowledge/` — verified facts vs hypotheses
- `experiments/` — protocolled experiments (protocol → results → conclusion)
- `assets/` — test inputs (person photos, garment references)
