from pathlib import Path
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

base = Path(__file__).resolve().parents[2]
df = pd.read_csv(base / "Données" / "dataset_videos_meteo.csv", sep=";", low_memory=False)
out = base / "Resultats" / "modeles_meteo"
out.mkdir(parents=True, exist_ok=True)

df["datetime_video"] = pd.to_datetime(df["datetime_video"], errors="coerce")
df["annee"] = df["datetime_video"].dt.year
df["ruche"] = df["ruche"].astype(str).str.replace("nap-mag1255", "", regex=False)

jeux = {
    "complet": df,
    "sans_2202_2024": df[~((df["ruche"] == "2202") & (df["annee"] == 2024))]
}

configs = {
    "IC_moyen": ["temperature_moy_30min", "humidite_moy_30min", "pression_moy_30min", "vent_moyen_IC_30min"],
    "IC_rafale": ["temperature_moy_30min", "humidite_moy_30min", "pression_moy_30min", "rafales_IC_max_30min"],
    "MR_moyen": ["temperature_moy_30min", "humidite_moy_30min", "pression_moy_30min", "vent_moyen_MR_30min"],
    "MR_rafale": ["temperature_moy_30min", "humidite_moy_30min", "pression_moy_30min", "rafales_MR_max_30min"]
}

corrs = []
vifs = []

for version, d0 in jeux.items():
    for nom, cols in configs.items():
        d = d0[cols].apply(pd.to_numeric, errors="coerce").dropna()
        c = d.corr(method="spearman")
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                corrs.append([version, nom, a, b, c.loc[a, b]])
        x = (d - d.mean()) / d.std()
        for i, col in enumerate(cols):
            vifs.append([version, nom, col, variance_inflation_factor(x.values, i)])

pd.DataFrame(corrs, columns=["version", "modele", "variable_1", "variable_2", "spearman"]).to_csv(out / "colinearite_spearman.csv", sep=";", index=False)
pd.DataFrame(vifs, columns=["version", "modele", "variable", "VIF"]).to_csv(out / "colinearite_VIF.csv", sep=";", index=False)
