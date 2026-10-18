"""Синтетична сім’я #1450; фото-приймання pending."""
from фото_тип_синтетика import *

def reader_build():
    r, m, receipt = fixture()
    values = (dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[r]), m, receipt)
    with tempfile.TemporaryDirectory() as td:
        assert З.читати_фото_тип(td)["records"] == {}
        with zipfile.ZipFile(io.BytesIO(), "w") as z:
            names = []; Б._покласти_фото_тип(z, td, names); assert names == []
        for name, value in zip(Ф.ФАЙЛИ, values):
            Path(td, name + ".gz").write_bytes(gzip.compress(Ф.канонічні_байти(value), mtime=0))
        got = З.читати_фото_тип(td)
        assert got["ledger"] == dict(records=1, projected=1, unprojected=0, controls_excluded=0)
        assert З.фото_тип_речі(dict(id="synthetic", фото=[r["image"]["url"]]), got["records"])["visible_item_type"]["item_type"] == "shirt"
        assert З.фото_тип_речі(dict(id="synthetic", фото=[]), got["records"])["visible_item_type"]["status"] == "unknown"
        assert З.фото_тип_речі(dict(id="other"), got["records"]) == {}
        with zipfile.ZipFile(io.BytesIO(), "w") as z:
            names = []; Б._покласти_фото_тип(z, td, names)
            assert names == [n + ".gz" for n in Ф.ФАЙЛИ]
            for n in names:
                assert z.read(n) == Path(td, n).read_bytes()

if __name__ == "__main__":
    reader_build()
    print("SYNTHETIC_ONLY reader_build: PASS; photo acceptance pending")
