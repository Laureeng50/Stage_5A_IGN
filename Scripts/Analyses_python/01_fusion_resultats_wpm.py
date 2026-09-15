from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parents[2]
dossier = base / "Resultats" / "resultats_videos"
sortie = base / "Resultats" / "resultats_WPM_complet.csv"

fichiers = [f for f in sorted(dossier.glob("*.csv")) if not f.name.startswith("PARTIEL_")]
if not fichiers:
    raise FileNotFoundError("Aucun fichier résultat trouvé")

tables = []
for fichier in fichiers:
    df = pd.read_csv(fichier, sep=None, engine="python", encoding="utf-8-sig")
    df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
    tables.append(df)

resultats = pd.concat(tables, ignore_index=True)

if resultats.duplicated(["ruche", "nom_fichier"]).any():
    raise RuntimeError("Des vidéos apparaissent plusieurs fois")

for col in ["chemin", "chemin_serveur", "output_path"]:
    if col in resultats.columns:
        resultats = resultats.drop(columns=col)

tri = [c for c in ["ruche", "date", "heure", "nom_fichier"] if c in resultats.columns]
resultats = resultats.sort_values(tri)
resultats.to_csv(sortie, sep=";", index=False, encoding="utf-8-sig")

print(len(resultats), "vidéos")
print(resultats["statut"].value_counts())
print("Phases :", pd.to_numeric(resultats["nb_phases_WPM"], errors="coerce").fillna(0).sum())
