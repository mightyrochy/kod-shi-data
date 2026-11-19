"""Запуск джерела/жнива_кадри.py з ATR на відеокарті: ONNX-сесії Leffa жорстко на CPU, продукт не чіпаємо.
Запуск з теки `джерела`: python ../аудит/проби/річ_кадр_варіант_кадри/запуск_gpu.py <ключі жнива_кадри.py>
(як `аудит/проби/річ_колір_перезбір_0411/запуск_gpu.py`)."""
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
скрипт = Path.cwd() / "жнива_кадри.py"
sys.path.insert(0, str(Path.cwd()))
sys.argv = [str(скрипт), *sys.argv[1:]]
runpy.run_path(str(скрипт), run_name="__main__")
