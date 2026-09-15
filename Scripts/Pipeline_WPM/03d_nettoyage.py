# Supprime les fichiers temporaires du serveur uniquement après validation de la récupération locale du lot.
from pathlib import Path
from urllib.parse import quote
import shutil
import subprocess
import time

base = Path(r"D:\Algorithme\pipeline_wpm")
tmp = base / "en_cours"
user = "LEnguehard"
server = "DEL2304S004"
winscp = Path(r"C:\Program Files (x86)\WinSCP\WinSCP.com")
mdp_file = base / "mdp_winscp.txt"
remote = "/home/LEnguehard/code/DANSE/pipeline_wpm"


def lancer_winscp(script, essais=20, attente=60):
    for tentative in range(1, essais + 1):
        try:
            p = subprocess.run([str(winscp), f"/script={script}"], timeout=180)
            if p.returncode == 0:
                return
        except subprocess.TimeoutExpired:
            pass
        print(f"Connexion échouée ({tentative}/{essais})")
        if tentative < essais:
            time.sleep(attente)
    raise RuntimeError("Nettoyage impossible.")


recuperation_ok = tmp / "recuperation_ok.txt"
if not recuperation_ok.exists():
    raise RuntimeError("Récupération non validée. Le serveur ne sera pas nettoyé.")

mdp = quote(mdp_file.read_text(encoding="utf-8").strip(), safe="")
winscp_script = tmp / "winscp_nettoyage.txt"
winscp_script.write_text(
    "\n".join([
        "option batch abort",
        "option confirm off",
        f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
        f"call rm -rf {remote}/videos/*",
        f"call rm -rf {remote}/outputs/*",
        f"call rm -f {remote}/lot.csv {remote}/hyperparametres.json {remote}/03b_batch_serveur.py",
        f"call rm -f {remote}/lancer_batch.sh {remote}/batch_started.txt",
        f"call rm -f {remote}/resultats.csv {remote}/status.csv {remote}/batch.log",
        f"call rm -f {remote}/nohup_batch.log {remote}/pipeline_ok.txt",
        "exit",
    ]),
    encoding="utf-8",
)

print("Nettoyage du serveur...")
lancer_winscp(winscp_script)
shutil.rmtree(tmp)
tmp.mkdir()
print("Nettoyage terminé.")
