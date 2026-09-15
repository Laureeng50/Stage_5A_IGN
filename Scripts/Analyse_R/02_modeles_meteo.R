library(glmmTMB)
library(DHARMa)

set.seed(123)
df <- read.csv(file.path("Données", "dataset_videos_meteo.csv"), sep = ";")
out <- file.path("Resultats", "modeles_meteo")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

df$datetime_video <- as.POSIXct(df$datetime_video)
df <- df[df$statut %in% c("reussite", "reussite_sans_phase"), ]
df$ruche <- gsub("nap-mag1255", "", df$ruche)
df$annee <- as.numeric(format(df$datetime_video, "%Y"))
df$mois <- as.numeric(format(df$datetime_video, "%m"))
df$heure_num <- as.numeric(format(df$datetime_video, "%H"))
df$date <- as.Date(df$datetime_video)
df$presence <- as.integer(df$nb_phases_WPM > 0)
df$saison <- factor(ifelse(df$mois %in% 3:5, "printemps", ifelse(df$mois %in% 6:8, "ete", ifelse(df$mois %in% 9:11, "automne", "hiver"))))
df <- df[df$heure_num >= 9 & df$heure_num <= 20, ]
df$heure <- factor(df$heure_num)

df$groupe <- NA
df$groupe[df$ruche == "2202" & (is.na(df$categorie_traitement) | df$categorie_traitement == "")] <- "G1"
df$groupe[df$categorie_traitement == "2202_LED5"] <- "G2"
df$groupe[df$categorie_traitement == "2202_LED4_FAIBLE"] <- "G3"
df$groupe[df$categorie_traitement == "2202_LED_NON_APPARENTE"] <- "G4"
df$groupe[df$categorie_traitement == "2202_CAMERA_DECALEE_A"] <- "G5"
df$groupe[df$categorie_traitement == "2202_OK"] <- "G6"
df$groupe[df$categorie_traitement == "2203_OK"] <- "G7"
df$groupe[df$categorie_traitement == "2203_FLOU"] <- "G8"
df$groupe[df$ruche == "2206" & (is.na(df$categorie_traitement) | df$categorie_traitement == "")] <- "G9"
df$groupe <- factor(df$groupe)
df$ruche_date <- interaction(df$ruche, df$date, drop = TRUE)
df$pluie <- as.integer(df$pluie_1h_precedente > 0)
df$activite_electrique <- as.integer(df$lightning_activity_1h > 0)

a <- df$direction_IC_30min * pi / 180
df$direction_IC_sin <- sin(a); df$direction_IC_cos <- cos(a)
a <- df$direction_MR_30min * pi / 180
df$direction_MR_sin <- sin(a); df$direction_MR_cos <- cos(a)

for (x in c("temperature_moy_30min", "humidite_moy_30min", "pression_moy_30min", "vent_moyen_IC_30min", "rafales_IC_max_30min", "vent_moyen_MR_30min", "rafales_MR_max_30min")) df[[paste0(x, "_z")]] <- as.numeric(scale(df[[x]]))

choix <- expand.grid(version = c("complet", "sans_2202_2024"), source = c("IC", "MR"), vent = c("moyen", "rafale"), reponse = c("presence", "intensite"), stringsAsFactors = FALSE)
modeles <- list(); resumes <- data.frame(); coeffs <- data.frame(); tests <- data.frame(); diagnostics <- data.frame()

for (i in seq_len(nrow(choix))) {
  c <- choix[i, ]
  d <- df
  if (c$version == "sans_2202_2024") d <- d[!(d$ruche == "2202" & d$annee == 2024), ]

  if (c$source == "IC") {
    vent <- if (c$vent == "moyen") "vent_moyen_IC_30min_z" else "rafales_IC_max_30min_z"
    dsin <- "direction_IC_sin"; dcos <- "direction_IC_cos"; extra <- character(0)
  } else {
    vent <- if (c$vent == "moyen") "vent_moyen_MR_30min_z" else "rafales_MR_max_30min_z"
    dsin <- "direction_MR_sin"; dcos <- "direction_MR_cos"; extra <- "activite_electrique"
  }

  y <- if (c$reponse == "presence") "presence" else "nb_phases_WPM"
  famille <- if (c$reponse == "presence") binomial() else truncated_nbinom2()
  vars <- c(y, "temperature_moy_30min_z", "humidite_moy_30min_z", "pression_moy_30min_z", vent, dsin, dcos, "pluie", "saison", "heure", "groupe", "ruche_date", extra)
  d <- droplevels(d[complete.cases(d[, vars]), ])
  if (c$reponse == "intensite") d <- droplevels(d[d$nb_phases_WPM > 0, ])

  termes <- c("temperature_moy_30min_z", "humidite_moy_30min_z", "pression_moy_30min_z", vent, dsin, dcos, "pluie", "saison", "heure", "groupe", extra)
  f <- as.formula(paste(y, "~", paste(termes, collapse = " + "), "+ (1 | ruche_date)"))
  m <- glmmTMB(f, family = famille, data = d)
  nom <- paste(c$reponse, c$source, c$vent, c$version, sep = "_")
  modeles[[nom]] <- m

  resumes <- rbind(resumes, data.frame(modele = nom, n = nrow(d), AIC = AIC(m), convergence = m$fit$convergence, Hessienne_OK = m$sdr$pdHess))
  co <- summary(m)$coefficients$cond
  z <- data.frame(modele = nom, terme = rownames(co), beta = co[, "Estimate"], SE = co[, "Std. Error"], p_value = co[, "Pr(>|z|)"])
  z$IC95_inf <- z$beta - 1.96 * z$SE; z$IC95_sup <- z$beta + 1.96 * z$SE
  z$ratio <- exp(z$beta); z$ratio_IC95_inf <- exp(z$IC95_inf); z$ratio_IC95_sup <- exp(z$IC95_sup)
  coeffs <- rbind(coeffs, z)

  effets <- list(direction = c(dsin, dcos), saison = "saison", heure = "heure", groupe = "groupe")
  if (c$source == "MR") effets$activite_electrique <- "activite_electrique"
  for (nom_effet in names(effets)) {
    tr <- setdiff(termes, effets[[nom_effet]])
    m0 <- glmmTMB(as.formula(paste(y, "~", paste(tr, collapse = " + "), "+ (1 | ruche_date)")), family = famille, data = d)
    a0 <- anova(m0, m)
    tests <- rbind(tests, data.frame(modele = nom, effet = nom_effet, Chisq = a0$Chisq[2], ddl = a0$`Chi Df`[2], p_value = a0$`Pr(>Chisq)`[2]))
  }

  r <- simulateResiduals(m, n = 500)
  o <- if (c$reponse == "intensite") testOutliers(r, type = "bootstrap", nBoot = 250) else testOutliers(r)
  diagnostics <- rbind(diagnostics, data.frame(modele = nom, uniformite_p = testUniformity(r)$p.value, dispersion = testDispersion(r)$statistic, dispersion_p = testDispersion(r)$p.value, outliers_p = o$p.value))
}

write.csv(resumes, file.path(out, "resume_modeles.csv"), row.names = FALSE)
write.csv(coeffs, file.path(out, "coefficients_modeles.csv"), row.names = FALSE)
write.csv(tests, file.path(out, "tests_globaux.csv"), row.names = FALSE)
write.csv(diagnostics, file.path(out, "diagnostics_modeles.csv"), row.names = FALSE)
saveRDS(modeles, file.path(out, "modeles_meteo.rds"))
