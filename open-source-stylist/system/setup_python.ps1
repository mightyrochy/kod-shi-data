$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
python -m pip install -r (Join-Path $projectRoot "requirements.txt")

# InsightFace declares the CPU distribution as a dependency. Both ONNX Runtime
# distributions expose the same Python package, so reinstall the GPU wheel last.
python -m pip install --force-reinstall --no-deps "onnxruntime-gpu==1.23.2"

python -c "import onnxruntime as ort; providers=ort.get_available_providers(); print('ONNX Runtime providers:', providers); assert 'CUDAExecutionProvider' in providers"
