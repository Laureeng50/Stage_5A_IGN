from pathlib import Path
from urllib.parse import quote
import os
import subprocess
import sys
import time
import pandas as pd

repo = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
tmp = base / "en_cours"
sortie = repo / "Resultats_traitement"
resultats = sortie / "resultats_videos"
waggle_lots = sortie / "waggle_phases" / "lots"

user = os.environ.get("WPM_USER", "USER")
server = os.environ.get("WPM_SERVER", "SERVER")
winscp = Path(os.environ.get("WINSCP_PATH", r"C:\Program Files (x86)\WinSCP\WinSCP.com"))
mdp_file = Path(os.environ.get("WPM_PASSWORD_FILE", str(base / "mdp_winscp.txt")))
remote = os.environ.get("WPM_REMOTE", "/path/to/pipeline_wpm")

script_03a = base / "03a_transfert.py"
script_03c = base / "03c_recuperation.py"
script_03d = base / "03d_nettoyage.py"
lot_path = Path(sys.argv[1])

def telecharger(remote_file, local_file):
    if local_file.exists():
        local_file.unlink()
    mdp = quote(mdp_file.read_text(encoding="utf-8").strip(), safe="")
    script = tmp / "winscp_check.txt"
    script.write_text("\n".join([
        "option batch continue",
        "option confirm off",
        f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
        f'get "{remote}/{remote_file}" "{local_file}"',
        "exit"
    ]), encoding="utf-8")
    subprocess.run([str(winscp), f"/script={script}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return local_file.exists()

subprocess.run([sys.executable, str(script_03a), str(lot_path)], check=True)
lot = pd.read_csv(tmp / "lot_en_cours.csv", sep=";", encoding="utf-8-sig")
lot.columns = [c.replace("\ufeff", "").strip() for c in lot.columns]
nom_lot = str(lot["nom_lot"].iloc[0])
ruche_courte = str(lot["ruche"].iloc[0]).replace("nap-mag1255", "")

print("Attente du serveur :", nom_lot)
while not telecharger("pipeline_ok.txt", tmp / "pipeline_ok_check.txt"):
    log_local = tmp / "batch_check.log"
    if telecharger("batch.log", log_local):
        lignes = log_local.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        print("En cours -", lignes[-1] if lignes else "calcul en cours")
    else:
        print("Calcul en cours")
    time.sleep(30)

subprocess.run([sys.executable, str(script_03c)], check=True)
subprocess.run([sys.executable, str(script_03d)], check=True)

csv_final = resultats / f"resultats_{ruche_courte}_{nom_lot}.csv"
csv_waggle = waggle_lots / f"waggle_phases_{ruche_courte}_{nom_lot}.csv"
if not csv_final.exists() or not csv_waggle.exists():
    raise RuntimeError("Sorties finales introuvables")

print("Lot terminé :", nom_lot)
