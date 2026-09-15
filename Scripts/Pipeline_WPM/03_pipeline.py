# Pilote le traitement d'un lot : transfert, attente du calcul serveur, récupération des résultats puis nettoyage.
from pathlib import Path
from urllib.parse import quote
import subprocess
import sys
import time
import pandas as pd

base = Path(r"D:\Algorithme\pipeline_wpm")
python = Path(r"D:\Algorithme\waggle_phase_mapper-main\.venv\Scripts\python.exe")
tmp = base / "en_cours"
sortie = Path(r"D:\Algorithme\Resultats_traitement")
resultats = sortie / "resultats_videos"
waggle_lots = sortie / "waggle_phases" / "lots"

user = "LEnguehard"
server = "DEL2304S004"
winscp = Path(r"C:\Program Files (x86)\WinSCP\WinSCP.com")
mdp_file = base / "mdp_winscp.txt"
remote = "/home/LEnguehard/code/DANSE/pipeline_wpm"

script_03a = base / "03a_transfert.py"
script_03c = base / "03c_recuperation.py"
script_03d = base / "03d_nettoyage.py"
lot_path = Path(sys.argv[1])


def format_duree(secondes):
    if secondes < 60:
        return f"{secondes:.1f} s"
    if secondes < 3600:
        return f"{secondes / 60:.1f} min"
    return f"{secondes / 3600:.2f} h"


def telecharger(remote_file, local_file):
    if local_file.exists():
        local_file.unlink()

    mdp = quote(mdp_file.read_text(encoding="utf-8").strip(), safe="")
    script = tmp / "winscp_check.txt"
    script.write_text(
        "\n".join([
            "option batch continue",
            "option confirm off",
            f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
            f'get "{remote}/{remote_file}" "{local_file}"',
            "exit",
        ]),
        encoding="utf-8",
    )
    subprocess.run(
        [str(winscp), f"/script={script}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return local_file.exists()


debut_pipeline = time.time()

print("Transfert et lancement du lot")
t0 = time.time()
subprocess.run([str(python), str(script_03a), str(lot_path)], check=True)
temps_transfert = time.time() - t0

lot = pd.read_csv(tmp / "lot_en_cours.csv", sep=";", encoding="utf-8-sig")
lot.columns = [c.replace("\ufeff", "").strip() for c in lot.columns]
nom_lot = str(lot["nom_lot"].iloc[0])
ruche_courte = str(lot["ruche"].iloc[0]).replace("nap-mag1255", "")

print("Attente du serveur :", nom_lot)
t0 = time.time()

while not telecharger("pipeline_ok.txt", tmp / "pipeline_ok_check.txt"):
    log_local = tmp / "batch_check.log"
    if telecharger("batch.log", log_local):
        lignes = log_local.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
        print("En cours -", lignes[-1] if lignes else "calcul en cours")
    else:
        print("Calcul en cours...")
    time.sleep(30)

temps_calcul = time.time() - t0

print("Récupération des résultats")
t0 = time.time()
subprocess.run([str(python), str(script_03c)], check=True)
temps_recup = time.time() - t0

print("Nettoyage du serveur")
t0 = time.time()
subprocess.run([str(python), str(script_03d)], check=True)
temps_nettoyage = time.time() - t0

csv_final = resultats / f"resultats_{ruche_courte}_{nom_lot}.csv"
csv_waggle = waggle_lots / f"waggle_phases_{ruche_courte}_{nom_lot}.csv"

print("\nBilan du lot")
print("Lot :", nom_lot)
print("Ruche :", ruche_courte)
print("Vidéos :", len(lot))
print("Transfert + lancement :", format_duree(temps_transfert))
print("Calcul serveur :", format_duree(temps_calcul))
print("Récupération :", format_duree(temps_recup))
print("Nettoyage :", format_duree(temps_nettoyage))
print("Temps total :", format_duree(time.time() - debut_pipeline))
print("Résultats vidéo :", csv_final)
print("Waggle phases :", csv_waggle)
