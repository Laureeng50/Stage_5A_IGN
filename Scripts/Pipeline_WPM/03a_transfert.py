from pathlib import Path
from urllib.parse import quote
import os
import shutil
import subprocess
import sys
import time
import pandas as pd

repo = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent
tmp = base / "en_cours"
user = os.environ.get("WPM_USER", "USER")
server = os.environ.get("WPM_SERVER", "SERVER")
winscp = Path(os.environ.get("WINSCP_PATH", r"C:\Program Files (x86)\WinSCP\WinSCP.com"))
mdp_file = Path(os.environ.get("WPM_PASSWORD_FILE", str(base / "mdp_winscp.txt")))
remote = os.environ.get("WPM_REMOTE", "/path/to/pipeline_wpm")
remote_python = os.environ.get("WPM_REMOTE_PYTHON", "python")
script_serveur = base / "03b_batch_serveur.py"
lot_path = Path(sys.argv[1])
hyper_dir = repo / "Calibration" / "Hyperparametres"
video_root = Path(os.environ.get("WPM_VIDEO_ROOT", "."))

if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir()

def lancer_winscp(script, essais=20, attente=60):
    for tentative in range(1, essais + 1):
        p = subprocess.run([str(winscp), f"/script={script}"])
        if p.returncode == 0:
            return
        print(f"Connexion échouée ({tentative}/{essais})")
        if tentative < essais:
            time.sleep(attente)
    raise RuntimeError("Impossible de contacter le serveur")

df = pd.read_csv(lot_path, sep=None, engine="python", encoding="utf-8-sig")
df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]

nom_hyperparam = str(df["hyperparametre_file"].iloc[0])
hyperparam = hyper_dir / nom_hyperparam
if not hyperparam.exists():
    raise FileNotFoundError(hyperparam)

tmp_lot = tmp / "lot_en_cours.csv"
df.to_csv(tmp_lot, sep=";", index=False, encoding="utf-8-sig")

videos = []
for i in df.index:
    chemin = Path(str(df.at[i, "chemin"]))
    if not chemin.is_absolute():
        chemin = video_root / chemin
    video = chemin if chemin.suffix.lower() == ".mp4" else chemin / str(df.at[i, "nom_fichier"])
    if not video.exists():
        raise FileNotFoundError(video)
    videos.append(video)

lancer = tmp / "lancer_batch.sh"
lancer.write_text(
    "#!/bin/bash\n"
    f"cd {remote} || exit 1\n"
    "if [ -f batch_started.txt ]; then exit 0; fi\n"
    "touch batch_started.txt\n"
    "rm -f resultats.csv status.csv batch.log nohup_batch.log pipeline_ok.txt\n"
    f"nohup {remote_python} 03b_batch_serveur.py > nohup_batch.log 2>&1 &\n",
    encoding="utf-8",
    newline="\n"
)

mdp = quote(mdp_file.read_text(encoding="utf-8").strip(), safe="")
script_transfert = tmp / "winscp_transfert.txt"
lignes = [
    "option batch abort",
    "option confirm off",
    f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
    f"call rm -rf {remote}",
    f"call mkdir -p {remote}/videos {remote}/outputs",
    f'put "{tmp_lot}" "{remote}/lot.csv"',
    f'put "{hyperparam}" "{remote}/hyperparametres.json"',
    f'put "{script_serveur}" "{remote}/03b_batch_serveur.py"',
    f'put "{lancer}" "{remote}/lancer_batch.sh"'
]
lignes.extend(f'put "{video}" "{remote}/videos/"' for video in videos)
lignes.append("exit")
script_transfert.write_text("\n".join(lignes), encoding="utf-8")

print(len(videos), "vidéos à transférer")
print("Lot :", df["nom_lot"].iloc[0])
print("Hyperparamètres :", nom_hyperparam)
lancer_winscp(script_transfert)

script_lancement = tmp / "winscp_lancement.txt"
script_lancement.write_text("\n".join([
    "option batch abort",
    "option confirm off",
    f"open scp://{user}:{mdp}@{server}/ -hostkey=*",
    f"call chmod +x {remote}/lancer_batch.sh",
    f"call {remote}/lancer_batch.sh",
    "exit"
]), encoding="utf-8")

lancer_winscp(script_lancement)
print("Transfert terminé et batch lancé")
