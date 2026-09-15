# Lance WPM sur les vidéos du lot, gère les traitements parallèles et relance une fois les vidéos en échec.
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import time
import pandas as pd

base = Path("/home/LEnguehard/code/DANSE/pipeline_wpm")
videos_dir = base / "videos"
outputs_dir = base / "outputs"
lot_csv = base / "lot.csv"
hyperparam = base / "hyperparametres.json"
resultats_csv = base / "resultats.csv"
status_csv = base / "status.csv"
batch_log = base / "batch.log"

wpm = "/home/LEnguehard/code/DANSE/.venv/bin/wpm"
lat = "46.153895"
lon = "-0.689021"
tz = "Europe/Paris"

n_parallel = 5
n_parallel_retry = 2
timeout_1 = 22 * 60
timeout_2 = 60 * 60
min_speed = "0.5"
delai_lancement = 15


def log(txt):
    print(txt, flush=True)
    with batch_log.open("a", encoding="utf-8") as f:
        f.write(str(txt) + "\n")


def count_phases(out):
    for f in out.rglob("waggle_phases.csv"):
        try:
            with f.open(encoding="utf-8") as fichier:
                return max(0, sum(1 for _ in fichier) - 1)
        except Exception:
            return ""
    return 0


def clean_output(out):
    a_garder = {"waggle_phases.csv", "detection.log", "batch_log.txt"}
    for f in out.rglob("*"):
        if f.is_file() and f.name not in a_garder:
            try:
                f.unlink()
            except OSError:
                pass


def run_video(row, passage, timeout_s, delay=0):
    nom = str(row["nom_fichier"])
    video = videos_dir / nom
    out = outputs_dir / Path(nom).stem
    out.mkdir(parents=True, exist_ok=True)

    if delay:
        time.sleep(delay)

    cmd = [
        "timeout", str(timeout_s), wpm, "detection",
        "--detection__min_speed", min_speed,
        "--output_path", str(out),
        "--hyperparameters_file_path", str(hyperparam),
        "--", str(video), lat, lon, tz,
    ]

    t0 = time.time()
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    temps = round(time.time() - t0, 1)
    (out / "batch_log.txt").write_text(p.stdout, encoding="utf-8", errors="ignore")

    if p.returncode == 124:
        statut = "echec_timeout"
    elif "Detection speed too slow" in p.stdout:
        statut = "echec_detection_slow"
    elif p.returncode == 0:
        statut = "reussite"
    else:
        statut = "echec"

    nb = count_phases(out)
    if statut == "reussite" and nb == 0:
        statut = "reussite_sans_phase"

    clean_output(out)

    resultat = row.to_dict()
    resultat.update({
        "passage": passage,
        "statut": statut,
        "nb_phases_WPM": nb,
        "temps_s": temps,
        "chemin_serveur": str(video),
        "output_path": str(out),
    })
    return resultat


df = pd.read_csv(lot_csv, sep=";", encoding="utf-8-sig")
df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
outputs_dir.mkdir(exist_ok=True)
batch_log.write_text("", encoding="utf-8")

log(f"Début batch : {len(df)} vidéos")
res_passage_1 = []

with ThreadPoolExecutor(max_workers=n_parallel) as ex:
    futures = [
        ex.submit(run_video, row.copy(), "passage_1", timeout_1, (k % n_parallel) * delai_lancement)
        for k, (_, row) in enumerate(df.iterrows())
    ]
    for i, future in enumerate(as_completed(futures), 1):
        r = future.result()
        res_passage_1.append(r)
        log(f"[{i}/{len(df)}] {r['statut']} | {r['temps_s']} s | {r['nb_phases_WPM']} phases | {r['nom_fichier']}")
        pd.DataFrame(res_passage_1).to_csv(status_csv, sep=";", index=False, encoding="utf-8-sig")

retry = [r for r in res_passage_1 if r["statut"] in {"echec_timeout", "echec_detection_slow", "echec"}]
log(f"Passage 2 : {len(retry)} vidéos à relancer")
res_passage_2 = []

if retry:
    with ThreadPoolExecutor(max_workers=n_parallel_retry) as ex:
        futures = [
            ex.submit(run_video, pd.Series(r), "passage_2", timeout_2, (k % n_parallel_retry) * delai_lancement)
            for k, r in enumerate(retry)
        ]
        for i, future in enumerate(as_completed(futures), 1):
            r = future.result()
            res_passage_2.append(r)
            log(f"[retry {i}/{len(retry)}] {r['statut']} | {r['temps_s']} s | {r['nb_phases_WPM']} phases | {r['nom_fichier']}")
            pd.DataFrame(res_passage_1 + res_passage_2).to_csv(status_csv, sep=";", index=False, encoding="utf-8-sig")

retry_par_nom = {str(r["nom_fichier"]): r for r in res_passage_2}
res_final = []

for r1 in res_passage_1:
    r2 = retry_par_nom.get(str(r1["nom_fichier"]))
    r = (r2 if r2 is not None else r1).copy()
    temps_2 = float(r2["temps_s"]) if r2 is not None else 0.0
    r["temps_passage_1_s"] = float(r1["temps_s"])
    r["temps_passage_2_s"] = temps_2
    r["a_ete_relancee"] = r2 is not None
    r["temps_total_video_s"] = round(float(r1["temps_s"]) + temps_2, 1)
    res_final.append(r)

final = pd.DataFrame(res_final).sort_values("nom_fichier")
final.to_csv(resultats_csv, sep=";", index=False, encoding="utf-8-sig")
(base / "pipeline_ok.txt").write_text("OK", encoding="utf-8")

log("Batch terminé")
log(str(final["statut"].value_counts()))
