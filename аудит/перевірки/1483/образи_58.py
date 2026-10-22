import io,tarfile,subprocess,sys,os,json,hashlib
дер=sys.argv[1]; вих=sys.argv[2]
os.chdir(дер+"/джерела"); sys.path.insert(0,os.path.abspath("."))
import warnings; warnings.simplefilter("ignore")
import pipeline as PL, протокол as П
a=tarfile.open(fileobj=io.BytesIO(subprocess.run(["git","-C","/home/user/kod-shi-data","archive","origin/claude/zhyvi-58","аудит/живі_58"],capture_output=True,check=True).stdout))
рез={}
for ч in a:
    if ч.isfile() and ч.name.endswith(".txt") and "ОБРАЗИ_V1" in ч.name:
        т=a.extractfile(ч).read().decode("utf-8","replace"); відп=т.split("── ВІДПОВІДЬ",1)[-1].split("\n",1)[-1].rstrip("\n")
        try:
            о=PL.образи_з_тексту(відп)
            з=json.dumps(о,ensure_ascii=False,sort_keys=True,default=str)
        except Exception as e: з="ВИНЯТОК "+type(e).__name__
        рез[ч.name]=з
json.dump(рез,open(вих,"w",encoding="utf-8"),ensure_ascii=False)
print(len(рез),"відповідей")
