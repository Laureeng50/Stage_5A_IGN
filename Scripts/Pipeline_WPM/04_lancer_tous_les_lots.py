from pathlib import Path
import subprocess
import sys
import time
import pandas as pd

repo = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
dossier_lots = base / "lots"
sortie = repo / "Resultats_traitement"
resultats = sortie / "resultats_videos"
waggle_lots = sortie / "waggle_phases" / "lots"
validation = sortie / "validation_lots"
script_03 = base / "03_pipeline.py"

for dossier in [resultats, waggle_lots, validation]:
    dossier.mkdir(parents=True, exist_ok=True)

resume = pd.read_csv(dossier_lots / "resume_creation_lots.csv", sep=";", encoding="utf-8-sig")
if len(resume) != 9:
    raise RuntimeError(f"9 groupes attendus, {len(resume)} trouvés")

lots = []
for dossier in resume["dossier"]:
    lots.extend(sorted(Path(dossier).glob("*.csv")))

print("Lots trouvés :", len(lots))
debut = time.time()

for i, lot in enumerate(lots, 1):
    df = pd.read_csv(lot, sep=None, engine="python", encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
    nom_lot = str(df["nom_lot"].iloc[0])
    ruche = str(df["ruche"].iloc[0]).replace("nap-mag1255", "")
    fichier_ok = validation / f"{ruche}_{nom_lot}.ok"
    fichier_resultat = resultats / f"resultats_{ruche}_{nom_lot}.csv"
    fichier_waggle = waggle_lots / f"waggle_phases_{ruche}_{nom_lot}.csv"

    print(f"Lot {i}/{len(lots)} : {nom_lot}")
    if fichier_ok.exists() and fichier_resultat.exists() and fichier_waggle.exists():
        print("Déjà récupéré et validé")
        continue

    subprocess.run([sys.executable, str(script_03), str(lot)], check=True)
    if not fichier_ok.exists() or not fichier_resultat.exists() or not fichier_waggle.exists():
        raise RuntimeError("Sorties incomplètes : " + nom_lot)

    print("Temps total écoulé :", round((time.time() - debut) / 3600, 2), "heures")

print("Tous les lots disponibles sont terminés")
