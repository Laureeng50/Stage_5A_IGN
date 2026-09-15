from pathlib import Path
import pandas as pd

repo = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
table = repo / "Données" / "BDD_inventaire.csv"
hyper_dir = repo / "Calibration" / "Hyperparametres"
dossier_lots = base / "lots"
taille_lot = 50

groupes = [
    ("nap-mag12552202", "2202_LED2_LED4", ["ok - LED apparente n°2", "ok - LED apparente n°4"], "best_hyperparameters_DUR03_ED50_DX3_SLOPE1_50_GAP40_SR20.json"),
    ("nap-mag12552202", "2202_LED5", ["ok - LED apparente n°5"], "best_hyperparameters_2202_LED5_MIX2.json"),
    ("nap-mag12552202", "2202_LED4_FAIBLE", ["ok - LED apparente n°4 (1/5 LED très faible)"], "best_hyperparameters_2202_LED4faible_BASE_DX60.json"),
    ("nap-mag12552202", "2202_LED_NON_APPARENTE", ["ok - LED non apparente"], "best_hyperparameters_DX20_R2.json"),
    ("nap-mag12552202", "2202_CAMERA_DECALEE_A", ["ok - Setup camera décalé A (6 LED, apparente n°5)"], "best_hyperparameters_DX20_R1.json"),
    ("nap-mag12552202", "2202_OK", ["ok"], "best_hyperparameters_DX20_R3.json"),
    ("nap-mag12552203", "2203_OK", ["ok"], "best_hyperparameters_2203_DUR05_ED40_DX15_SLOPE2_35_GAP30_SR30.json"),
    ("nap-mag12552203", "2203_FLOU", ["ok mais qualité vidéo faible (flou)"], "best_hyperparameters_2203_DUR05_ED40_DX15_SLOPE2_35_GAP30_SR30.json"),
    ("nap-mag12552206", "2206_OK", ["ok"], "best_hyperparameters_2206_T1_DUR03_ED50_DX10_SLOPE1_60_GAP40_SR20.json")
]

df_total = pd.read_csv(table, low_memory=False)
df_total["commentaires"] = df_total["commentaires"].astype(str).str.replace("\xa0", " ", regex=False).str.strip()
df_total["Exploitabilité"] = df_total["Exploitabilité"].astype(str).str.strip()
resume = []

for ruche, categorie, commentaires, hyperparam_file in groupes:
    fichier_hyperparam = hyper_dir / hyperparam_file
    if not fichier_hyperparam.exists():
        raise FileNotFoundError(fichier_hyperparam)

    df = df_total[(df_total["ruche"] == ruche) & (df_total["commentaires"].isin(commentaires)) & (df_total["Exploitabilité"] == "Exploitable")].copy()
    if df.empty:
        raise ValueError("Aucune vidéo trouvée pour " + categorie)

    df = df.sort_values(["date", "heure"])
    df["heure_tmp"] = df["heure"].astype(str).str[:2]
    df = df.drop_duplicates(["ruche", "date", "heure_tmp"], keep="first").drop(columns="heure_tmp")

    hyperparam = Path(hyperparam_file).stem
    out = dossier_lots / f"{categorie}_{hyperparam}" / f"lots_{taille_lot}"
    out.mkdir(parents=True, exist_ok=True)
    for ancien in out.glob("*.csv"):
        ancien.unlink()

    for i in range(0, len(df), taille_lot):
        lot = df.iloc[i:i + taille_lot].copy()
        num = i // taille_lot + 1
        date_debut = str(lot["date"].iloc[0])[:10]
        date_fin = str(lot["date"].iloc[-1])[:10]
        nom_lot = f"{categorie}_LOT_{num:03d}_{len(lot)}_{date_debut}_{date_fin}"
        lot["nom_lot"] = nom_lot
        lot["taille_lot"] = taille_lot
        lot["hyperparametre"] = hyperparam
        lot["hyperparametre_file"] = hyperparam_file
        lot["categorie_traitement"] = categorie
        lot.to_csv(out / f"{nom_lot}.csv", index=False, encoding="utf-8-sig")

    nb_lots = (len(df) + taille_lot - 1) // taille_lot
    resume.append({"categorie": categorie, "ruche": ruche, "videos": len(df), "lots": nb_lots, "dossier": str(out)})
    print(categorie, ":", len(df), "vidéos,", nb_lots, "lots")

resume = pd.DataFrame(resume)
dossier_lots.mkdir(exist_ok=True)
resume.to_csv(dossier_lots / "resume_creation_lots.csv", sep=";", index=False, encoding="utf-8-sig")

if int(resume["videos"].sum()) != 8853:
    raise RuntimeError("Le total attendu est 8853 vidéos")
