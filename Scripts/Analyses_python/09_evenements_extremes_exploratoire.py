from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parents[2]
df = pd.read_csv(base / "Données" / "dataset_meteo_master.csv", sep=";")
df["datetime"] = pd.to_datetime(df["datetime"], format="mixed", dayfirst=True, errors="coerce")
df = df.dropna(subset=["datetime"])

for col in ["temperature_C", "vent_rafales_MR", "vent_rafales_IC", "pluie_1h_C", "lightning_activity_MR"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

rafale = df["vent_rafales_MR"].fillna(df["vent_rafales_IC"])
seuil_pluie = df.loc[df["pluie_1h_C"] > 0, "pluie_1h_C"].quantile(0.95)
seuil_vent = rafale.quantile(0.95)
seuil_chaleur = df["temperature_C"].quantile(0.95)

events = pd.DataFrame({
    "datetime": df["datetime"],
    "forte_pluie": df["pluie_1h_C"] >= seuil_pluie,
    "vent_fort": rafale >= seuil_vent,
    "forte_chaleur": df["temperature_C"] >= seuil_chaleur,
    "activite_electrique": df["lightning_activity_MR"] > 0
})

events = events[events.iloc[:, 1:].any(axis=1)]
events.to_csv(base / "Resultats" / "evenements_meteo_exploratoires.csv", sep=";", index=False, encoding="utf-8-sig")
