# Parcourt les lots des neuf groupes et lance uniquement ceux dont les résultats détaillés n'ont pas encore été récupérés et validés.
from pathlib import Path
import subprocess
import time
import pandas as pd

base = Path(r"D:\Algorithme\pipeline_wpm")
python = Path(r"D:\Algorithme\waggle_phase_mapper-main\.venv\Scripts\python.exe")
dossier_lots = base / "lots"
sortie = Path(r"D:\Algorithme\Resultats_traitement")
resultats = sortie / "resultats_videos"
waggle_lots = sortie / "waggle_phases" / "lots"
validation = sortie / "validation_lots"
script_03 = base / "03_pipeline.py"

for dossier in [resultats, waggle_lots, validation]:
    dossier.mkdir(parents=True, exist_ok=True)

resume = pd.read_csv(dossier_lots / "resume_creation_lots.csv", sep=";", encoding="utf-8-sig")
if len(resume) != 9:
    raise RuntimeError(f"9 groupes attendus, {len(resume)} trouvés dans le résumé des lots.")

lots = []
for dossier in resume["dossier"]:
    lots.extend(sorted(Path(dossier).glob("*.csv")))

print("Groupes trouvés :", len(resume))
print("Lots trouvés :", len(lots))
debut_total = time.time()

for i, lot in enumerate(lots, 1):
    df_lot = pd.read_csv(lot, sep=None, engine="python", encoding="utf-8-sig")
    df_lot.columns = [c.replace("\ufeff", "").strip() for c in df_lot.columns]

    nom_lot = str(df_lot["nom_lot"].iloc[0])
    ruche_courte = str(df_lot["ruche"].iloc[0]).replace("nap-mag1255", "")
    groupe = lot.parent.parent.name

    fichier_ok = validation / f"{ruche_courte}_{nom_lot}.ok"
    fichier_resultat = resultats / f"resultats_{ruche_courte}_{nom_lot}.csv"
    fichier_waggle = waggle_lots / f"waggle_phases_{ruche_courte}_{nom_lot}.csv"

    print(f"\nLot {i}/{len(lots)} : {nom_lot}")
    print("Groupe :", groupe)

    if fichier_ok.exists() and fichier_resultat.exists() and fichier_waggle.exists():
        print("Déjà récupéré et validé.")
        continue

    debut_lot = time.time()
    subprocess.run([str(python), str(script_03), str(lot)], check=True)

    if not fichier_ok.exists() or not fichier_resultat.exists() or not fichier_waggle.exists():
        raise RuntimeError(f"Sorties incomplètes après traitement : {nom_lot}")

    print("Lot terminé en", round((time.time() - debut_lot) / 3600, 2), "heures")
    print("Temps total écoulé :", round((time.time() - debut_total) / 3600, 2), "heures")

print("\nTous les lots disponibles sont terminés.")
