from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copyfile
import pickle
import socket
import feed, фід_розбір, таблиця_каталогу, таблиця_збирання

def blocked(*args, **kwargs):
    raise RuntimeError("network disabled")

socket.socket = socket.getaddrinfo = socket.create_connection = blocked
root = Path.cwd()
archive = root / "каталог_повний.xml.gz"
with TemporaryDirectory() as temp:
    copyfile(archive, Path(temp) / archive.name)
    path = feed.каталог_на_диску(str(Path(temp) / archive.stem))
    table = таблиця_збирання.зібрати(path, str(root / "джерела"))
    offers = фід_розбір.офери_фіду(path)
    catalogue = таблиця_каталогу.відновити(table, offers)["каталог"]
    with Path(__file__).with_name("catalogue.pkl").open("wb") as output:
        pickle.dump(catalogue, output)
    dress = next(o for o in offers if o["id"] == "ж-00408@feelyou.com.ua")
    with Path(__file__).with_name("dress.pkl").open("wb") as output:
        pickle.dump(dress, output)
print(len(catalogue))
