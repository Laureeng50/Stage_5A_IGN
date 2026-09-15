from pathlib import Path
from urllib.parse import quote
import os
import shutil
import subprocess
import time
import pandas as pd

repo = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
tmp = base / "en_cours"
sortie = repo / "Resultats_traitement"
resultats = sortie / "resultats_videos"
waggle_lots = sortie / "waggle_phases" / "lots"
waggle_individuels = sortie / "waggle_phases" / "individuels"
validation = sortie / "validation_lots"

user = os.environ.get("WPM_USER", "USER")
server = os.environ.get("WPM_SERVER", "SERVER")
winscp = Path(os.environ.get("WINSCP_PATH", r"C:\Program Files (x86)\WinSCP\WinSCP.com"))
mdp_file = Path(os.environ.get("WPM_PASSWORD_FILE", str(base / "mdp_winscp.txt")))
remote = os.environ.get("WPM_REMOTE", "/path/to/pipeline_wpm")

for dossier in [tmp, resultats, waggle_lots, waggle_individuels, validation]:
    dossier.mkdir(parents=True, exist_ok=True)

def lancer_winscp(script, essais=20, attente=60):
    for tentative in range(1, essais + 1):
        p = subprocess.run([str(winscp), f"/script={script}"])
        if p.returncode == 0:
            return
        print(f"Connexion échouée ({tentative}/{essais})")
        if tentative < essais:
            time.sleep(attente)
    raise RuntimeError("Récupération impossible")

def nettoyer_colonnes(df):
    df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
    return df

def dossier_video(fichier):
    for parent in fichier.parents:
        if parent.name.startswith("Record_"):
            return parent.name
    return None

df_lot = nettoyer_colonnes(pd.read_csv(tmp / "lot_en_cours.csv", sep=";", encoding="utf-8-sig"))
nom_lot = str(df_lot["nom_lot"].iloc[0])
ruche_courte = str(df_lot["ruche"].iloc[0]).replace("nap-mag1255", "")

csv_local = resultats / f"resultats_{ruche_courte}_{nom_lot}.csv"
csv_partiel = resultats / f"PARTIEL_resultats_{ruche_courte}_{nom_lot}.csv"
csv_waggle_lot = waggle_lots / f"waggle_phases_{ruche_courte}_{nom_lot}.csv"
fichier_ok = validation / f"{ruche_courte}_{nom_lot}.ok"
temp_waggle = tmp / "waggle_recup"

if temp_waggle.exists():
    shutil.rmtree(temp_waggle)
temp_waggle.mkdir()

for fichier in [csv_local, csv_partiel, csv_waggle_lot, fichier_ok]:
    if fichier.exists():
        fichier.unlink()

mdp = quote(mdp_file.read_text(encoding="utf-8").strip(), safe="")
winscp_script = tmp / "winscp_recuperation.txt"
winscp_script.write_text("\n".join([
    "option batch abort",
    "option confirm off",
    f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
    f'get "{remote}/resultats.csv" "{csv_local}"',
    f'get -filemask="waggle_phases.csv" "{remote}/outputs/*" "{str(temp_waggle)}\\"',
    "exit"
]), encoding="utf-8")

print("Récupération du lot :", nom_lot)
lancer_winscp(winscp_script)

if not csv_local.exists():
    raise FileNotFoundError("resultats.csv n'a pas été récupéré")

res = nettoyer_colonnes(pd.read_csv(csv_local, sep=";", encoding="utf-8-sig"))
tri = [c for c in ["date", "heure", "nom_fichier"] if c in res.columns]
if tri:
    res = res.sort_values(tri)
res.to_csv(csv_local, sep=";", index=False, encoding="utf-8-sig")

if len(res) != len(df_lot):
    csv_local.rename(csv_partiel)
    raise RuntimeError(f"Lot incomplet : {len(res)}/{len(df_lot)}")

res["nb_phases_WPM"] = pd.to_numeric(res["nb_phases_WPM"], errors="coerce").fillna(0)
positives = res.loc[res["nb_phases_WPM"] > 0, "nom_fichier"].astype(str)
fichiers_waggle = list(temp_waggle.rglob("waggle_phases.csv"))
dossiers_recuperes = {dossier_video(f) for f in fichiers_waggle}
manquants = [nom for nom in positives if Path(nom).stem not in dossiers_recuperes]
if manquants:
    raise RuntimeError(f"{len(manquants)} waggle_phases.csv manquants")

waggle_lot = []
for fichier in fichiers_waggle:
    nom_video = dossier_video(fichier)
    correspondance = df_lot[df_lot["nom_fichier"].astype(str).map(lambda x: Path(x).stem) == nom_video]
    if len(correspondance) != 1:
        raise RuntimeError("Impossible d'identifier la vidéo " + str(nom_video))

    info = correspondance.iloc[0]
    waggle = nettoyer_colonnes(pd.read_csv(fichier, sep=None, engine="python", encoding="utf-8-sig"))
    waggle.insert(0, "ruche", str(info["ruche"]))
    waggle.insert(1, "nom_fichier", str(info["nom_fichier"]))
    waggle.insert(2, "chemin", str(info["chemin"]))
    position = 3
    for colonne in ["date", "heure", "categorie_traitement", "hyperparametre_file", "nom_lot"]:
        if colonne in info.index:
            waggle.insert(position, colonne, info[colonne])
            position += 1

    csv_individuel = waggle_individuels / f"{ruche_courte}_{nom_video}_waggle_phases.csv"
    waggle.to_csv(csv_individuel, sep=";", index=False, encoding="utf-8-sig")
    waggle_lot.append(waggle)

nb_resume = int(res["nb_phases_WPM"].sum())
if waggle_lot:
    waggle_lot = pd.concat(waggle_lot, ignore_index=True)
    waggle_lot.to_csv(csv_waggle_lot, sep=";", index=False, encoding="utf-8-sig")
    nb_detail = len(waggle_lot)
else:
    nb_detail = 0
    pd.DataFrame().to_csv(csv_waggle_lot, sep=";", index=False, encoding="utf-8-sig")

if nb_detail != nb_resume:
    raise RuntimeError("Incohérence entre nb_phases_WPM et les waggle_phases récupérés")

shutil.rmtree(temp_waggle)
fichier_ok.write_text(f"lot={nom_lot}\nruche={ruche_courte}\nvideos={len(res)}\nphases={nb_detail}\n", encoding="utf-8")
(tmp / "recuperation_ok.txt").write_text(f"{nom_lot}\n{len(res)} vidéos\n{len(fichiers_waggle)} fichiers waggle_phases\n{nb_detail} phases détaillées\n", encoding="utf-8")

print("Vidéos récupérées :", len(res))
print("Fichiers waggle_phases :", len(fichiers_waggle))
print("Phases détaillées :", nb_detail)
