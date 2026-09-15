from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parents[2]
df = pd.read_csv(base / "Resultats" / "resultats_WPM_complet.csv", sep=";", low_memory=False)
out = base / "Resultats" / "figures_wpm"
out.mkdir(parents=True, exist_ok=True)

df["nb_phases_WPM"] = pd.to_numeric(df["nb_phases_WPM"], errors="coerce").fillna(0)
df["temps_total_video_s"] = pd.to_numeric(df.get("temps_total_video_s"), errors="coerce")

fig, axes = plt.subplots(2, 2, figsize=(9, 7))
statuts = df["statut"].replace({"reussite": "Avec phase", "reussite_sans_phase": "Sans phase"}).value_counts()
axes[0,0].bar(statuts.index, statuts.values)
axes[0,0].set_ylabel("Nombre de vidéos")
axes[0,0].tick_params(axis="x", rotation=20)
axes[0,1].hist(df["temps_total_video_s"].dropna() / 60, bins=50)
axes[0,1].set_xlabel("Temps de traitement (min)")
axes[1,0].hist(df["nb_phases_WPM"], bins=60)
axes[1,0].set_xlabel("Nombre de phases WPM par vidéo")
axes[1,1].scatter(df["nb_phases_WPM"], df["temps_total_video_s"] / 60, s=4, alpha=0.3)
axes[1,1].set_xlabel("Nombre de phases WPM")
axes[1,1].set_ylabel("Temps (min)")
plt.tight_layout()
plt.savefig(out / "bilan_traitement_WPM.png", dpi=300)
plt.close()
