from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parents[2]
df = pd.read_csv(base / "Données" / "dataset_videos_meteo.csv", sep=";", low_memory=False)
out = base / "Resultats" / "figures_temporelles"
out.mkdir(parents=True, exist_ok=True)

df = df[df["statut"].isin(["reussite", "reussite_sans_phase"])].copy()
df["datetime_video"] = pd.to_datetime(df["datetime_video"])
df["ruche"] = df["ruche"].astype(str).str.replace("nap-mag1255", "", regex=False)
df["annee"] = df["datetime_video"].dt.year
df["heure_num"] = df["datetime_video"].dt.hour
df["semaine"] = df["datetime_video"].dt.to_period("W").dt.start_time
df["presence"] = (df["nb_phases_WPM"] > 0).astype(int)

def profil_semaine(g):
    pos = g[g["nb_phases_WPM"] > 0]
    return pd.Series({"presence": 100 * g["presence"].mean(), "intensite": pos["nb_phases_WPM"].mean() if len(pos) else np.nan})

hebdo = df.groupby(["ruche", "annee", "semaine"]).apply(profil_semaine, include_groups=False).reset_index()

fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), sharey=True)
for ax, ruche in zip(axes, ["2202", "2203", "2206"]):
    d = hebdo[hebdo["ruche"] == ruche]
    for annee, g in d.groupby("annee"):
        ax.plot(g["semaine"], g["presence"], marker="o", markersize=2, label=str(annee))
    ax.set_title("Ruche " + ruche)
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=45)
axes[0].set_ylabel("Vidéos avec présence (%)")
axes[1].set_xlabel("Date")
axes[0].legend()
plt.tight_layout()
plt.savefig(out / "presence_saisonniere.png", dpi=300)
plt.close()

fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), sharey=True)
for ax, ruche in zip(axes, ["2202", "2203", "2206"]):
    d = hebdo[hebdo["ruche"] == ruche]
    for annee, g in d.groupby("annee"):
        ax.plot(g["semaine"], g["intensite"], marker="o", markersize=2, label=str(annee))
    ax.set_title("Ruche " + ruche)
    ax.tick_params(axis="x", rotation=45)
axes[0].set_ylabel("Nombre moyen de phases par vidéo positive")
axes[1].set_xlabel("Date")
axes[0].legend()
plt.tight_layout()
plt.savefig(out / "intensite_saisonniere.png", dpi=300)
plt.close()

d = df[(df["heure_num"] >= 9) & (df["heure_num"] <= 20)]
horaire = d.groupby(["ruche", "annee", "heure_num"]).apply(profil_semaine, include_groups=False).reset_index()

fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
for j, ruche in enumerate(["2202", "2203", "2206"]):
    x = horaire[horaire["ruche"] == ruche]
    for annee, g in x.groupby("annee"):
        axes[0, j].plot(g["heure_num"], g["presence"], marker="o", label=str(annee))
        axes[1, j].plot(g["heure_num"], g["intensite"], marker="o", label=str(annee))
    axes[0, j].set_title("Ruche " + ruche)
axes[0, 0].set_ylabel("Présence (%)")
axes[1, 0].set_ylabel("Phases par vidéo positive")
for ax in axes[1]: ax.set_xlabel("Heure")
axes[0, 0].legend()
plt.tight_layout()
plt.savefig(out / "cycle_journalier.png", dpi=300)
plt.close()
