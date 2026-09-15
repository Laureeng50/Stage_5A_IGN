from pathlib import Path
import pandas as pd

base = Path(__file__).resolve().parents[2]
meteo = base / "Données" / "Meteo"
ic_dir = meteo / "Infoclimat"
mr_dir = meteo / "MR"
out = meteo / "preparees"
out.mkdir(parents=True, exist_ok=True)

ic_files = sorted(ic_dir.glob("*.csv"))
mr_files = sorted(mr_dir.glob("*.csv"))

if not ic_files or not mr_files:
    raise FileNotFoundError("Les fichiers météo sources sont absents")

cols_ic = ["dh_utc", "temperature", "pression", "humidite", "vent_moyen", "vent_rafales", "vent_direction", "pluie_1h", "pluie_24h"]
ic = []
for fichier in ic_files:
    df = pd.read_csv(fichier, sep=";", skiprows=4, low_memory=False)
    df.columns = df.columns.str.strip()
    if "station_id" in df.columns:
        df = df[df["station_id"] != "string"]
    ic.append(df[cols_ic])

ic = pd.concat(ic, ignore_index=True)
ic.columns = ["datetime", "temperature_IC", "pression_IC", "humidite_IC", "vent_moyen_IC", "vent_rafales_IC", "vent_direction_IC", "pluie_IC_1h", "pluie_IC_24h"]
ic["datetime"] = pd.to_datetime(ic["datetime"], errors="coerce")
for col in ic.columns[1:]:
    ic[col] = pd.to_numeric(ic[col], errors="coerce")
ic = ic.dropna(subset=["datetime"]).sort_values("datetime").drop_duplicates("datetime")

cols_mr = ["Timestamps", "mm Precipitation", "Lightning Activity", "km Lightning Distance", "° Wind Direction", "m/s Wind Speed", "m/s Gust Speed", "°C Air Temperature", "kPa Atmospheric Pressure", "kPa Vapor Pressure", "kPa VPD"]
mr = []
for fichier in mr_files:
    df = pd.read_csv(fichier, skiprows=2, low_memory=False)
    df.columns = df.columns.str.strip()
    mr.append(df[cols_mr])

mr = pd.concat(mr, ignore_index=True)
mr.columns = ["datetime", "pluie_MR_15min", "lightning_activity_MR", "lightning_distance_MR", "vent_direction_MR", "vent_moyen_ms", "vent_rafales_ms", "temperature_MR", "pression_kPa", "vapor_MR", "vpd_MR"]
mr["datetime"] = pd.to_datetime(mr["datetime"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
for col in mr.columns[1:]:
    mr[col] = pd.to_numeric(mr[col], errors="coerce")
mr = mr.dropna(subset=["datetime"]).sort_values("datetime").drop_duplicates("datetime")
mr["pression_MR"] = mr["pression_kPa"] * 10
mr["vent_moyen_MR"] = mr["vent_moyen_ms"] * 3.6
mr["vent_rafales_MR"] = mr["vent_rafales_ms"] * 3.6
mr["humidite_MR"] = 100 * mr["vapor_MR"] / (mr["vapor_MR"] + mr["vpd_MR"])
mr["humidite_MR"] = mr["humidite_MR"].clip(0, 100)

pluie = mr.set_index("datetime")["pluie_MR_15min"].resample("1h", label="right", closed="right").sum().rename("pluie_MR_1h")
mr = mr.merge(pluie, left_on="datetime", right_index=True, how="left")

commun = pd.merge_asof(
    mr[["datetime", "humidite_MR"]].sort_values("datetime"),
    ic[["datetime", "humidite_IC"]].sort_values("datetime"),
    on="datetime",
    direction="nearest",
    tolerance=pd.Timedelta("10min")
).dropna()
commun = commun[(commun["datetime"] >= "2023-05-02") & (commun["datetime"] <= "2023-07-30 23:59:59")]

m_ic = commun["humidite_IC"].mean()
s_ic = commun["humidite_IC"].std()
m_mr = commun["humidite_MR"].mean()
s_mr = commun["humidite_MR"].std()
ic["humidite_IC_calibree"] = (m_mr + (ic["humidite_IC"] - m_ic) * s_mr / s_ic).clip(0, 100)

ic["temperature_C"] = ic["temperature_IC"]
ic["pression_C"] = ic["pression_IC"] - 7.5
ic["humidite_C"] = ic["humidite_IC_calibree"]
ic["pluie_1h_C"] = ic["pluie_IC_1h"]

avant_mr = ic[ic["datetime"] < mr["datetime"].min()][["datetime", "temperature_C", "pression_C", "humidite_C", "pluie_1h_C", "vent_moyen_IC", "vent_rafales_IC", "vent_direction_IC"]].copy()
avant_mr[["vent_moyen_MR", "vent_rafales_MR", "vent_direction_MR", "lightning_activity_MR", "lightning_distance_MR"]] = pd.NA

mr2 = mr[["datetime", "humidite_MR", "pluie_MR_1h", "vent_moyen_MR", "vent_rafales_MR", "vent_direction_MR", "lightning_activity_MR", "lightning_distance_MR"]].copy()
ic_ref = ic[["datetime", "temperature_C", "pression_C", "vent_moyen_IC", "vent_rafales_IC", "vent_direction_IC"]].copy()
mr2 = pd.merge_asof(mr2.sort_values("datetime"), ic_ref.sort_values("datetime"), on="datetime", direction="nearest", tolerance=pd.Timedelta("10min"))
mr2["humidite_C"] = mr2["humidite_MR"]
mr2["pluie_1h_C"] = mr2["pluie_MR_1h"]

master = pd.concat([avant_mr, mr2], ignore_index=True).sort_values("datetime").drop_duplicates("datetime")
cols = ["datetime", "temperature_C", "pression_C", "humidite_C", "pluie_1h_C", "vent_moyen_IC", "vent_rafales_IC", "vent_direction_IC", "vent_moyen_MR", "vent_rafales_MR", "vent_direction_MR", "lightning_activity_MR", "lightning_distance_MR"]
master = master[cols]

ic.to_csv(out / "infoclimat_prepare.csv", index=False, encoding="utf-8-sig")
mr.to_csv(out / "mr_prepare.csv", index=False, encoding="utf-8-sig")
master.to_csv(base / "Données" / "dataset_meteo_master.csv", sep=";", index=False, encoding="utf-8-sig")

print(master["datetime"].min(), master["datetime"].max(), len(master))
