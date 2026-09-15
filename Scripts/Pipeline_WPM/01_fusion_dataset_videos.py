from pathlib import Path
import pandas as pd

repo = Path(__file__).resolve().parents[2]
donnees = repo / "Données"
inventaire_path = donnees / "inventaire_videos.csv"
qualite_path = donnees / "Table_qualite_videos.xlsx"
sortie_path = donnees / "BDD_inventaire.csv"

inventaire = pd.read_csv(inventaire_path, sep=";")
qualite = pd.read_excel(qualite_path)
inventaire.columns = inventaire.columns.str.strip()
qualite.columns = qualite.columns.str.strip()

inventaire["date"] = pd.to_datetime(inventaire["date"], dayfirst=True, errors="coerce").dt.normalize()
qualite["date"] = pd.to_datetime(qualite["date"], dayfirst=True, errors="coerce").dt.normalize()
inventaire["heure"] = inventaire["nom_fichier"].str.extract(r"_(\d+-\d+-\d+)_csi0")[0].str.replace("-", ":", regex=False)

videos = inventaire.merge(qualite, on=["ruche", "date"], how="left")
videos.to_csv(sortie_path, index=False, encoding="utf-8-sig")

print("Vidéos dans l'inventaire :", len(inventaire))
print("Vidéos après fusion :", len(videos))
print("Vidéos sans correspondance qualité :", videos["commentaires"].isna().sum())
