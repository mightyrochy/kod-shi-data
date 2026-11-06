"""Запуск перезібрати.py з ATR на відеокарті: ONNX-сесії Leffa жорстко на CPU, продукт не чіпаємо."""
import os, runpy, site, sys
from pathlib import Path

for корінь in dict.fromkeys([*site.getsitepackages(), site.getusersitepackages()]):
    for тека in sorted((Path(корінь) / "nvidia").glob("*/bin")):
        os.add_dll_directory(str(тека))
        os.environ["PATH"] = str(тека) + os.pathsep + os.environ["PATH"]
import onnxruntime as ort

_стара = ort.InferenceSession.__init__


def _ініт(self, *арг, **кв):
    кв["providers"] = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    кв.pop("provider_options", None)
    _стара(self, *арг, **кв)


ort.InferenceSession.__init__ = _ініт
скрипт = Path(__file__).with_name("перезібрати.py")
sys.argv = [str(скрипт), *sys.argv[1:]]
runpy.run_path(str(скрипт), run_name="__main__")
