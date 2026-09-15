# Fusionne l'inventaire des vidéos avec la table de qualité pour créer la table utilisée par la suite du pipeline.
from pathlib import Path
import pandas as pd

base = Path(r"D:\Algorithme\pipeline_wpm")
tables = base / "tables"
tables.mkdir(exist_ok=True)

inventaire_path = tables / "inventaire_videos.csv"
qualite_path = tables / "Table_qualite_videos.xlsx"
sortie_path = tables / "Table_fusionnee_VF_videos.csv"

inventaire = pd.read_csv(inventaire_path, sep=";")
qualite = pd.read_excel(qualite_path)

inventaire.columns = inventaire.columns.str.strip()
qualite.columns = qualite.columns.str.strip()

inventaire["date"] = pd.to_datetime(inventaire["date"], dayfirst=True, errors="coerce").dt.normalize()
qualite["date"] = pd.to_datetime(qualite["date"], dayfirst=True, errors="coerce").dt.normalize()

inventaire["heure"] = (
    inventaire["nom_fichier"]
    .str.extract(r"_(\d+-\d+-\d+)_csi0")[0]
    .str.replace("-", ":", regex=False)
)

videos = inventaire.merge(qualite, on=["ruche", "date"], how="left")
videos.to_csv(sortie_path, index=False, encoding="utf-8-sig")

print("Vidéos dans l'inventaire :", len(inventaire))
print("Vidéos après fusion :", len(videos))
print("Vidéos sans correspondance qualité :", videos["commentaires"].isna().sum())

if len(inventaire) != len(videos):
    print("Attention : le nombre de lignes a changé pendant la fusion.")

resume = videos.groupby(["ruche", "commentaires"]).size().reset_index(name="nb_videos")
print("\nNombre de vidéos par ruche et commentaire :")
print(resume.to_string(index=False))
print("\nFichier créé :", sortie_path)
