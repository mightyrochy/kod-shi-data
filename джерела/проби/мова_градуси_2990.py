"""Друкує контракт, який вчить модель переводити градуси й відчуття у сім смуг."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М
if __name__ == "__main__":
    рядки = list(М._коди_розмови())
    смуга = next(р for р in рядки if р.startswith("- weather_band"))
    assert not any(р.startswith(("- temperature_c", "- weather_feel")) for р in рядки)
    assert all(код in смуга for код in ("deep_frost", "frost", "cold", "cool", "mild", "warm", "hot"))
    print(смуга)
    print("Модель віддає сім смуг; окремих полів градусів і відчуття немає")
