# Stage 5A IGN – GeoDanceHive / DANSE

Ce dépôt regroupe les principaux scripts, données dérivées et résultats produits pendant mon stage de fin d'études au LASTIG (IGN), dans le cadre du projet DANSE.

Le travail porte sur le traitement de vidéos issues des GeoDanceHive avec le Waggle Phase Mapper (WPM), puis sur l'analyse des variations temporelles de l'activité de recrutement détectée et de leurs relations avec les conditions météorologiques.

Le corpus étudié couvre les années 2022 à 2024 pour les ruches 2202, 2203 et 2206. Une vidéo de dix minutes par heure a été retenue pour le traitement massif, soit 8 853 vidéos.

## Organisation

```text
Stage_5A_IGN/
├── Calibration/
│   ├── BDD_calibration.xlsx
│   └── Hyperparametres/
├── Données/
│   ├── BDD_inventaire.csv
│   ├── dataset_meteo_master.csv
│   └── dataset_videos_meteo.csv
├── Resultats/
│   ├── resultats_WPM_complet.csv
│   └── waggle_phases_WPM_complet.csv
├── Scripts/
│   ├── Pipeline_WPM/
│   ├── Analyses_python/
│   └── Analyse_R/
├── .gitattributes
├── .gitignore
└── README.md
```

## Calibration du WPM

`Calibration/BDD_calibration.xlsx` contient les comptages manuels des vidéos de calibration et les résultats des configurations d'hyperparamètres testées.

Le dossier `Calibration/Hyperparametres/` contient les fichiers JSON retenus pour les groupes techniques G1 à G9.

| Groupe | Configuration utilisée |
| --- | --- |
| G1 | `best_hyperparameters_DUR03_ED50_DX3_SLOPE1_50_GAP40_SR20.json` |
| G2 | `best_hyperparameters_2202_LED5_MIX2.json` |
| G3 | `best_hyperparameters_2202_LED4faible_BASE_DX60.json` |
| G4 | `best_hyperparameters_DX20_R2.json` |
| G5 | `best_hyperparameters_DX20_R1.json` |
| G6 | `best_hyperparameters_DX20_R3.json` |
| G7 | `best_hyperparameters_2203_DUR05_ED40_DX15_SLOPE2_35_GAP30_SR30.json` |
| G8 | même configuration que G7 |
| G9 | `best_hyperparameters_2206_T1_DUR03_ED50_DX10_SLOPE1_60_GAP40_SR20.json` |

## Données

### `BDD_inventaire.csv`

Inventaire utilisé pour la sélection des vidéos. Il contient notamment la ruche, la date, l'heure, les informations de qualité et la catégorie technique associée à chaque enregistrement.

### `dataset_meteo_master.csv`

Série météorologique harmonisée construite à partir des données Infoclimat et de la station locale du Magneraud. Elle contient les variables retenues pour l'association avec les vidéos.

### `dataset_videos_meteo.csv`

Jeu de données utilisé pour les analyses temporelles et météorologiques. Chaque ligne correspond à une vidéo et regroupe les sorties WPM, les informations temporelles, le groupe technique et les variables météorologiques associées.


## Résultats WPM

### `resultats_WPM_complet.csv`

Table récapitulative à l'échelle des vidéos. Elle contient le statut du traitement, le nombre de phases frétillantes détectées et les informations associées au traitement.

### `waggle_phases_WPM_complet.csv`

Table détaillée contenant une ligne par phase frétillante détectée par WPM.

Ces deux fichiers sont suivis avec Git LFS.

## Scripts du pipeline WPM

Les scripts de `Scripts/Pipeline_WPM/` correspondent à la chaîne utilisée pour préparer les lots, lancer WPM sur le serveur de calcul, récupérer les sorties et contrôler les traitements.

| Script | Rôle |
| --- | --- |
| `01_fusion_dataset_videos.py` | Construction de `BDD_inventaire.csv` à partir de l'inventaire initial et de la table de qualité. |
| `02_creer_lots_multi_groupes.py` | Sélection d'une vidéo exploitable par heure, attribution des hyperparamètres et création des lots de 50 vidéos. |
| `03_pipeline.py` | Enchaînement du transfert, du traitement serveur, de la récupération et du nettoyage pour un lot. |
| `03a_transfert.py` | Préparation du lot et transfert des vidéos et fichiers nécessaires vers le serveur. |
| `03b_batch_serveur.py` | Exécution du WPM sur le serveur, traitements parallèles et seconde tentative pour les vidéos en échec. |
| `03c_recuperation.py` | Récupération des résultats, regroupement des `waggle_phases.csv` et contrôles de cohérence. |
| `03d_nettoyage.py` | Suppression des fichiers temporaires du serveur après validation de la récupération. |
| `04_lancer_tous_les_lots.py` | Parcours de l'ensemble des lots et reprise uniquement des lots non validés. |




## Scripts Python d'analyse

| Script | Rôle |
| --- | --- |
| `01_fusion_resultats_wpm.py` | Fusion des résultats WPM produits par lot en une table unique à l'échelle des vidéos. Les fichiers par lot ne sont pas versionnés. |
| `02_preparer_meteo.py` | Nettoyage des données Infoclimat et MR, harmonisation des unités et création de `dataset_meteo_master.csv`. |
| `03_comparer_sources_meteo.py` | Comparaison MR–Infoclimat sur la période commune : biais, MAE, RMSE et corrélations. |
| `04_associer_meteo_videos.py` | Association des variables météorologiques aux vidéos à partir des fenêtres temporelles définies dans le mémoire. |
| `05_colinearite.py` | Calcul des corrélations de Spearman et des VIF pour les principales variables météorologiques. |
| `06_figures_temporelles.py` | Profils descriptifs saisonniers et intra-journaliers de la présence et de l'intensité. |
| `07_bilan_wpm.py` | Bilan descriptif des statuts, temps de calcul et nombres de phases détectées. |
| `08_description_meteo.py` | Description des conditions météorologiques associées aux vidéos. |
| `09_evenements_extremes_exploratoire.py` | Repérage exploratoire d'épisodes de pluie forte, vent fort, chaleur et activité électrique. |

## Scripts R

Les analyses statistiques principales sont regroupées dans `Scripts/Analyse_R/`.

| Script | Rôle |
| --- | --- |
| `01_analyse_temporelle.R` | GLMM temporels, GAM saisonniers par ruche-année et GAM intra-journaliers par groupe technique. |
| `02_modeles_meteo.R` | Ajustement des 16 modèles météorologiques principaux, extraction des coefficients, tests globaux et diagnostics DHARMa. |
| `03_nonlinearites_breakpoints.R` | Comparaison des formes linéaires et non linéaires et recherche des points de rupture pour la température, l'humidité et la pression. |
| `04_analyse_pluie.R` | Analyse de la présence de pluie, des quantités positives, des classes Q90–Q95 et ≥Q95 et des décalages de 1–2 h et 2–3 h. |
| `05_figures_modeles.R` | Figures de synthèse à partir des sorties des modèles météorologiques et des analyses de précipitations. |

Les scripts R utilisent des chemins relatifs et doivent être lancés depuis la racine du dépôt.

## Bibliothèques principales

Python : `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `statsmodels`.

R : `glmmTMB`, `mgcv`, `DHARMa`, `splines`, `ggplot2`.


## Données archivées

Les vidéos utilisées pour la calibration manuelle sont déposées sur Zenodo.

DOI Zenodo : à ajouter.
