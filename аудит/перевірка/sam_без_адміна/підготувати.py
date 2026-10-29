# -*- coding: utf-8 -*-
"""Завантажує відкриті ваги у профіль поточного користувача, без токенів."""
import hashlib
import json
import os
from pathlib import Path
import urllib.request


def головна():
    """Фіксує ревізії, розміри й SHA-256 завантажень для повторення середовища."""
    import truststore
    truststore.inject_into_ssl()
    from huggingface_hub import hf_hub_download, snapshot_download
    корінь = Path.home() / ".cache/liusterko/sam"
    опис = []
    for назва, ревізія in [
            ("IDEA-Research/grounding-dino-tiny", "a2bb814dd30d776dcf7e30523b00659f4f141c71"),
            ("facebook/sam-vit-base", "70c1a07f894ebb5b307fd9eaaee97b9dfc16068f")]:
        print("Ваги:", назва, flush=True)
        тека = Path(snapshot_download(назва, revision=ревізія, token=False,
                                     allow_patterns=["*.json", "*.safetensors", "vocab.txt"], max_workers=2))
        for файл in тека.rglob("*"):
            if файл.is_file():
                опис.append(dict(джерело=назва, ревізія=ревізія, файл=файл.name,
                                 байтів=файл.stat().st_size,
                                 sha256=hashlib.sha256(файл.read_bytes()).hexdigest()))
    for ім in ["parsing_atr.onnx", "parsing_lip.onnx"]:
        print("Ваги:", ім, flush=True)
        файл = Path(hf_hub_download("franciszzj/Leffa", "humanparsing/" + ім,
                    revision="61d3390f444506f052feedb0b243cd5369c29c89", token=False))
        ціль = корінь / "Leffa/ckpts/humanparsing" / ім
        ціль.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copyfile(файл, ціль)
        опис.append(dict(джерело="franciszzj/Leffa", ревізія="61d3390f444506f052feedb0b243cd5369c29c89",
                         файл=ім, байтів=ціль.stat().st_size,
                         sha256=hashlib.sha256(ціль.read_bytes()).hexdigest()))
    ревізія = "05a259104b6927607776c7edb3e86b75406f20aa"
    if not (корінь / "Leffa/preprocess/humanparsing/run_parsing.py").exists():
        with urllib.request.urlopen("https://api.github.com/repos/franciszzj/Leffa/git/trees/" + ревізія + "?recursive=1", timeout=30) as відповідь:
            дерево = json.load(відповідь)
        for запис in дерево["tree"]:
            ім = запис["path"]
            if запис["type"] != "blob" or not ім.startswith("preprocess/humanparsing/") or not ім.endswith(".py"):
                continue
            ціль = корінь / "Leffa" / ім
            ціль.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen("https://raw.githubusercontent.com/franciszzj/Leffa/" + ревізія + "/" + ім, timeout=30) as відповідь:
                ціль.write_bytes(відповідь.read())
    Path(__file__).with_name("ваги.json").write_text(json.dumps(опис, ensure_ascii=False, indent=2), encoding="utf-8")
    (корінь / "готово").write_text("GroundingDINO + SAM, локальні ваги завантажено\n", encoding="utf-8")
    print("Готово, байтів:", sum(р["байтів"] for р in опис), flush=True)


if __name__ == "__main__":
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    головна()
