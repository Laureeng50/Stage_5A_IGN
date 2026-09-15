from pathlib import Path
import numpy as np
import pandas as pd

base = Path(__file__).resolve().parents[2]
videos = pd.read_csv(base / "Resultats" / "resultats_WPM_complet.csv", sep=";", low_memory=False)
meteo = pd.read_csv(base / "Données" / "dataset_meteo_master.csv", sep=";", low_memory=False)

videos["datetime_video"] = pd.to_datetime(videos["date"].astype(str) + " " + videos["heure"].astype(str), format="mixed", dayfirst=True, errors="coerce")
meteo["datetime"] = pd.to_datetime(meteo["datetime"], format="mixed", dayfirst=True, errors="coerce")
meteo = meteo.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

for col in meteo.columns:
    if col != "datetime":
        meteo[col] = pd.to_numeric(meteo[col], errors="coerce")

def direction(x):
    x = x.dropna()
    if len(x) == 0:
        return np.nan
    a = np.deg2rad(x)
    return np.rad2deg(np.arctan2(np.sin(a).mean(), np.cos(a).mean())) % 360

temps = meteo["datetime"].to_numpy(dtype="datetime64[ns]")
pluie = meteo[meteo["pluie_1h_C"].notna()][["datetime", "pluie_1h_C"]].reset_index(drop=True)
temps_pluie = pluie["datetime"].to_numpy(dtype="datetime64[ns]")

lignes = []
for t in videos["datetime_video"]:
    if pd.isna(t):
        lignes.append({})
        continue

    t64 = np.datetime64(t)
    debut30 = t64 - np.timedelta64(30, "m")
    debut1h = t64 - np.timedelta64(1, "h")
    i30 = np.searchsorted(temps, debut30, side="right")
    i1h = np.searchsorted(temps, debut1h, side="right")
    fin = np.searchsorted(temps, t64, side="right")
    m30 = meteo.iloc[i30:fin]
    m1h = meteo.iloc[i1h:fin]

    r = {
        "temperature_moy_30min": m30["temperature_C"].mean(),
        "pression_moy_30min": m30["pression_C"].mean(),
        "humidite_moy_30min": m30["humidite_C"].mean(),
        "vent_moyen_IC_30min": m30["vent_moyen_IC"].mean(),
        "rafales_IC_moy_30min": m30["vent_rafales_IC"].mean(),
        "rafales_IC_max_30min": m30["vent_rafales_IC"].max(),
        "direction_IC_30min": direction(m30["vent_direction_IC"]),
        "vent_moyen_MR_30min": m30["vent_moyen_MR"].mean(),
        "rafales_MR_moy_30min": m30["vent_rafales_MR"].mean(),
        "rafales_MR_max_30min": m30["vent_rafales_MR"].max(),
        "direction_MR_30min": direction(m30["vent_direction_MR"]),
        "n_obs_IC_30min": m30["vent_moyen_IC"].notna().sum(),
        "n_obs_MR_30min": m30["vent_moyen_MR"].notna().sum()
    }

    act = m1h["lightning_activity_MR"]
    r["lightning_activity_1h"] = act.sum() if act.notna().any() else np.nan
    dist = m1h.loc[(m1h["lightning_activity_MR"] > 0) & (m1h["lightning_distance_MR"] > 0), "lightning_distance_MR"]
    r["lightning_distance_min_1h"] = dist.min() if len(dist) else np.nan
    r["n_obs_lightning_1h"] = act.notna().sum()

    p = np.searchsorted(temps_pluie, t64, side="right") - 1
    if p >= 0:
        delai = (t - pluie.loc[p, "datetime"]).total_seconds() / 60
        if delai <= 60:
            r["pluie_1h_precedente"] = pluie.loc[p, "pluie_1h_C"]
            r["heure_pluie"] = pluie.loc[p, "datetime"]
            r["delai_pluie_min"] = delai

    lignes.append(r)

met = pd.DataFrame(lignes)
df = pd.concat([videos.reset_index(drop=True), met.reset_index(drop=True)], axis=1)
df.to_csv(base / "Données" / "dataset_videos_meteo.csv", sep=";", index=False, encoding="utf-8-sig")
print(len(df), "vidéos")
