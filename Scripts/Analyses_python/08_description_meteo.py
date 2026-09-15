from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parents[2]
df = pd.read_csv(base / "Données" / "dataset_videos_meteo.csv", sep=";", low_memory=False)
out = base / "Resultats" / "description_meteo"
out.mkdir(parents=True, exist_ok=True)

df["datetime_video"] = pd.to_datetime(df["datetime_video"])
df["mois"] = df["datetime_video"].dt.month
df["heure"] = df["datetime_video"].dt.hour
df["semaine"] = df["datetime_video"].dt.to_period("W").dt.start_time

variables = [
    ("temperature_moy_30min", "Température (°C)"),
    ("humidite_moy_30min", "Humidité relative (%)"),
    ("pression_moy_30min", "Pression (hPa)"),
    ("vent_moyen_MR_30min", "Vent moyen MR (km/h)"),
    ("rafales_MR_max_30min", "Rafales MR (km/h)")
]

fig, axes = plt.subplots(len(variables), 2, figsize=(11, 12))
for i, (col, label) in enumerate(variables):
    d1 = df.groupby("semaine")[col].agg(["median", lambda x: x.quantile(.25), lambda x: x.quantile(.75)]).reset_index()
    axes[i,0].plot(d1["semaine"], d1["median"])
    axes[i,0].fill_between(d1["semaine"], d1["<lambda_0>"], d1["<lambda_1>"], alpha=.2)
    axes[i,0].set_ylabel(label)
    d2 = df.groupby("heure")[col].agg(["median", lambda x: x.quantile(.25), lambda x: x.quantile(.75)]).reset_index()
    axes[i,1].plot(d2["heure"], d2["median"])
    axes[i,1].fill_between(d2["heure"], d2["<lambda_0>"], d2["<lambda_1>"], alpha=.2)
axes[-1,0].set_xlabel("Date")
axes[-1,1].set_xlabel("Heure")
plt.tight_layout()
plt.savefig(out / "profils_meteo.png", dpi=300)
plt.close()

for source in ["IC", "MR"]:
    col = "direction_IC_30min" if source == "IC" else "direction_MR_30min"
    x = pd.to_numeric(df[col], errors="coerce").dropna()
    bins = np.arange(0, 361, 22.5)
    hist, edges = np.histogram(x, bins=bins)
    angles = np.deg2rad((edges[:-1] + edges[1:]) / 2)
    ax = plt.subplot(111, polar=True)
    ax.bar(angles, hist, width=np.deg2rad(22.5), align="center")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    plt.tight_layout()
    plt.savefig(out / f"rose_vent_{source}.png", dpi=300)
    plt.close()
