from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

base = Path(__file__).resolve().parents[2]
meteo = base / "Données" / "Meteo" / "preparees"
out = base / "Resultats" / "comparaison_meteo"
out.mkdir(parents=True, exist_ok=True)

ic = pd.read_csv(meteo / "infoclimat_prepare.csv")
mr = pd.read_csv(meteo / "mr_prepare.csv")
ic["datetime"] = pd.to_datetime(ic["datetime"])
mr["datetime"] = pd.to_datetime(mr["datetime"])

ic = ic[(ic["datetime"] >= "2023-05-02") & (ic["datetime"] <= "2023-07-30 23:59:59")].copy()
mr = mr[(mr["datetime"] >= "2023-05-02") & (mr["datetime"] <= "2023-07-30 23:59:59")].copy()

def circ(x):
    x = x.dropna()
    if len(x) == 0:
        return np.nan
    a = np.deg2rad(x)
    return np.rad2deg(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) % 360

def agreger(df, source):
    df = df.set_index("datetime")
    if source == "IC":
        return pd.DataFrame({
            "temperature_IC": df["temperature_IC"].resample("30min").mean(),
            "pression_IC": df["pression_IC"].resample("30min").mean(),
            "humidite_IC": df["humidite_IC"].resample("30min").mean(),
            "vent_moyen_IC": df["vent_moyen_IC"].resample("30min").mean(),
            "vent_rafales_IC": df["vent_rafales_IC"].resample("30min").max(),
            "vent_direction_IC": df["vent_direction_IC"].resample("30min").apply(circ)
        })
    return pd.DataFrame({
        "temperature_MR": df["temperature_MR"].resample("30min").mean(),
        "pression_MR": df["pression_MR"].resample("30min").mean(),
        "humidite_MR": df["humidite_MR"].resample("30min").mean(),
        "vent_moyen_MR": df["vent_moyen_MR"].resample("30min").mean(),
        "vent_rafales_MR": df["vent_rafales_MR"].resample("30min").max(),
        "vent_direction_MR": df["vent_direction_MR"].resample("30min").apply(circ)
    })

merge = agreger(ic, "IC").join(agreger(mr, "MR"), how="inner")
paires = [
    ("temperature_IC", "temperature_MR", "temperature"),
    ("pression_IC", "pression_MR", "pression"),
    ("humidite_IC", "humidite_MR", "humidite"),
    ("vent_moyen_IC", "vent_moyen_MR", "vent_moyen"),
    ("vent_rafales_IC", "vent_rafales_MR", "rafales")
]

res = []
for a, b, nom in paires:
    d = merge[[a, b]].dropna()
    res.append({
        "variable": nom,
        "n": len(d),
        "biais_MR_moins_IC": (d[b] - d[a]).mean(),
        "MAE": mean_absolute_error(d[a], d[b]),
        "RMSE": mean_squared_error(d[a], d[b]) ** 0.5,
        "Pearson": d[a].corr(d[b], method="pearson"),
        "Spearman": d[a].corr(d[b], method="spearman")
    })

angle = merge[["vent_direction_IC", "vent_direction_MR"]].dropna()
ecart = np.abs((angle["vent_direction_MR"] - angle["vent_direction_IC"] + 180) % 360 - 180)

pluie_ic = ic.set_index("datetime")["pluie_IC_1h"]
pluie_mr = mr.set_index("datetime")["pluie_MR_1h"]
pluie_h = pd.concat([pluie_ic.resample("1h").last(), pluie_mr.resample("1h").last()], axis=1).dropna()
pluie_j = pd.concat([pluie_ic.resample("1D").sum(), pluie_mr.resample("1D").sum()], axis=1).dropna()

pd.DataFrame(res).to_csv(out / "comparaison_MR_IC.csv", sep=";", index=False, encoding="utf-8-sig")
pd.DataFrame({
    "indicateur": ["direction_moyenne", "direction_mediane", "pluie_h_pearson", "pluie_j_pearson", "pluie_j_spearman"],
    "valeur": [ecart.mean(), ecart.median(), pluie_h.corr(method="pearson").iloc[0, 1], pluie_j.corr(method="pearson").iloc[0, 1], pluie_j.corr(method="spearman").iloc[0, 1]]
}).to_csv(out / "comparaisons_complementaires.csv", sep=";", index=False, encoding="utf-8-sig")

print(pd.DataFrame(res))
print("Direction :", ecart.mean(), ecart.median())
