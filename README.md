# Stage ingénieure de recherche IGN 

Ce dépôt regroupe les principaux scripts, données dérivées et résultats produits pendant mon stage de fin d'études au LASTIG (IGN), dans le cadre du projet DANSE.

Le travail porte sur le traitement de vidéos issues des GeoDanceHive avec le Waggle Phase Mapper (WPM), puis sur l'analyse des variations temporelles de l'activité de recrutement détectée et de leurs relations avec les conditions météorologiques.


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
│   ├── waggle_phases_WPM_complet.csv
│   └── Statistiques/
│       ├── 01_temporel/
│       ├── 02_comparaison_meteo/
│       ├── 03_modeles_meteo/
│       └── 04_pluie/
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



### Fichiers sources non inclus

Les fichiers bruts utilisés pour construire l'inventaire et les séries météorologiques ne sont pas versionnés dans ce dépôt. Les jeux de données préparés nécessaires aux analyses sont fournis dans `Données/`. Les scripts de préparation sont conservés pour documenter les traitements réalisés.

## Résultats WPM

### `resultats_WPM_complet.csv`

Table récapitulative à l'échelle des vidéos. Elle contient le statut du traitement, le nombre de phases frétillantes détectées et les informations associées au traitement.

### `waggle_phases_WPM_complet.csv`

Table détaillée contenant une ligne par phase frétillante détectée par WPM.

## Résultats statistiques

Le dossier `Resultats/Statistiques/` regroupe les principales tables produites pendant les analyses et utilisées pour les résultats et les annexes du mémoire. Elles sont conservées afin de garder une trace directe des sorties statistiques sans devoir relancer les modèles.

### `01_temporel/`

| Fichier | Contenu |
| --- | --- |
| `statistiques_saisonnieres.csv` | Statistiques hebdomadaires de présence et d'intensité par ruche et année. |
| `statistiques_horaires.csv` | Statistiques de présence et d'intensité selon l'heure. |
| `diagnostics_glmm_dharma.csv` | Diagnostics DHARMa des modèles temporels. |
| `diagnostics_k_gam.csv` | Contrôle de la dimension des lissages des GAM. |
| `profils_horaires_observes.csv` | Profils horaires observés par groupe technique. |
| `profils_mensuels_observes.csv` | Profils mensuels observés par groupe technique. |
| `sensibilite_globale_groupes.csv` | Tests globaux du modèle d'intensité intégrant les groupes techniques. |
| `groupes_g1_g9.csv` | Résumé descriptif des neuf groupes techniques. |
| `tests_gam_par_ruche.csv` | Résultats des GAM temporels par ruche. |
| `tests_glmm_lrt_par_ruche.csv` | Tests du rapport de vraisemblance des GLMM temporels. |

### `02_comparaison_meteo/`

| Fichier | Contenu |
| --- | --- |
| `donnees_comparees_mr_ic_30min.csv` | Données MR et Infoclimat appariées à 30 minutes sur la période commune. |
| `resume_comparaison_mr_ic.csv` | Biais, MAE, RMSE et corrélations entre MR et Infoclimat. |
| `resume_direction_vent.csv` | Écarts angulaires entre les directions du vent des deux sources. |
| `resume_pluie_journaliere.csv` | Comparaison des précipitations après agrégation journalière. |

### `03_modeles_meteo/`

| Fichier | Contenu |
| --- | --- |
| `correlations_meteo.csv` | Corrélations de Spearman utilisées pour le contrôle de la colinéarité. |
| `vif_modeles.csv` | VIF des variables utilisées dans les modèles météorologiques. |
| `vif_temperature_humidite.csv` | Contrôle complémentaire du VIF pour la température et l'humidité. |
| `resume_modeles.csv` | Résumé des 16 modèles météorologiques principaux. |
| `coefficients_modeles.csv` | Coefficients, rapports d'effet et intervalles des modèles principaux. |
| `diagnostics_modeles.csv` | Diagnostics des 16 modèles météorologiques. |
| `tests_globaux_modeles.csv` | Tests globaux des effets à plusieurs coefficients. |
| `variances_ruche_date.csv` | Variance de l'intercept aléatoire ruche × date. |
| `contributions_propres.csv` | Tests de contribution propre des variables non linéaires. |
| `tests_nonlinearite.csv` | Comparaison entre formulations linéaires et splines. |
| `predictions_courbes.csv` | Prédictions utilisées pour représenter les relations non linéaires. |
| `tests_nonlinearite_vent.csv` | Tests des formes non linéaires du vent. |
| `points_rupture.csv` | Points de rupture estimés pour les variables testées. |
| `predictions_points_rupture.csv` | Prédictions associées aux modèles avec point de rupture. |
| `profils_points_rupture.csv` | Profils de vraisemblance utilisés pour l'incertitude des points de rupture. |
| `profils_second_point_temperature.csv` | Profils testés pour un second point de rupture thermique. |
| `second_point_temperature.csv` | Résumé des essais d'un second point de rupture pour la température. |

### `04_pluie/`

| Fichier | Contenu |
| --- | --- |
| `descriptif_pluie.csv` | Description des observations associées à des précipitations. |
| `modeles_pluie_deux_parties.csv` | Résultats des modèles pluie sèche/pluvieuse et quantité positive. |
| `coefficients_classes_pluie.csv` | Coefficients des classes de précipitations par rapport au temps sec. |
| `tests_globaux_classes_pluie.csv` | Tests globaux des classes de précipitations. |
| `descriptif_classes_pluie.csv` | Statistiques descriptives des classes de pluie. |
| `seuils_pluie.csv` | Valeurs des seuils de pluie utilisés pour les classes principales. |
| `sensibilite_seuils_q75_q90_q95.csv` | Analyse de sensibilité à plusieurs quantiles de pluie forte. |
| `tendance_pluie_positive.csv` | Test d'une relation continue avec la quantité de pluie parmi les épisodes pluvieux. |

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



### Configuration du pipeline

Le pipeline nécessite l'accès aux vidéos originales et au serveur de calcul. Les paramètres propres à la machine sont définis par des variables d'environnement : `WPM_VIDEO_ROOT`, `WPM_USER`, `WPM_SERVER`, `WPM_PASSWORD_FILE`, `WPM_REMOTE`, `WPM_REMOTE_PYTHON` et `WINSCP_PATH`.

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


## Données de calibration

Les données utilisées pour la calibration du WPM sont archivées sur Zenodo :

https://doi.org/10.5281/zenodo.21488928
