library(glmmTMB)
library(splines)

df <- read.csv(file.path("Données", "dataset_videos_meteo.csv"), sep = ";")
meteo <- read.csv(file.path("Données", "dataset_meteo_master.csv"), sep = ";")
out <- file.path("Resultats", "analyse_pluie")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

df$datetime_video <- as.POSIXct(df$datetime_video, format = "%Y-%m-%d %H:%M:%S", tz = "Europe/Paris")
meteo$datetime <- as.POSIXct(meteo$datetime, format = "%d/%m/%Y %H:%M", tz = "Europe/Paris")
meteo$pluie_1h_C <- as.numeric(meteo$pluie_1h_C)
meteo <- meteo[!is.na(meteo$datetime) & !is.na(meteo$pluie_1h_C), ]
meteo <- meteo[order(meteo$datetime), ]

df <- df[df$statut %in% c("reussite", "reussite_sans_phase"), ]
df$ruche <- gsub("nap-mag1255", "", df$ruche)
df$annee <- as.numeric(format(df$datetime_video, "%Y"))
df$mois <- as.numeric(format(df$datetime_video, "%m"))
df$heure_num <- as.numeric(format(df$datetime_video, "%H"))
df$date <- as.Date(df$datetime_video)
df <- df[df$heure_num >= 9 & df$heure_num <= 20, ]
df$presence <- as.integer(df$nb_phases_WPM > 0)
df$saison <- factor(ifelse(df$mois %in% 3:5, "printemps", ifelse(df$mois %in% 6:8, "ete", "automne")))
df$heure <- factor(df$heure_num)
df$ruche_date <- interaction(df$ruche, df$date, drop = TRUE)
df$activite_electrique <- as.integer(df$lightning_activity_1h > 0)

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

a <- df$direction_IC_30min * pi / 180
df$direction_IC_sin <- sin(a)
df$direction_IC_cos <- cos(a)
a <- df$direction_MR_30min * pi / 180
df$direction_MR_sin <- sin(a)
df$direction_MR_cos <- cos(a)

df$temperature_z <- as.numeric(scale(df$temperature_moy_30min))
df$humidite_z <- as.numeric(scale(df$humidite_moy_30min))
df$pression_z <- as.numeric(scale(df$pression_moy_30min))
df$rafale_IC_z <- as.numeric(scale(df$rafales_IC_max_30min))
df$rafale_MR_z <- as.numeric(scale(df$rafales_MR_max_30min))

extraire_pluie <- function(cible) {
  idx <- findInterval(as.numeric(cible), as.numeric(meteo$datetime))
  val <- rep(NA_real_, length(idx))
  ok <- idx > 0
  delai <- rep(Inf, length(idx))
  delai[ok] <- as.numeric(cible[ok]) - as.numeric(meteo$datetime[idx[ok]])
  ok <- ok & delai >= 0 & delai <= 3600
  val[ok] <- meteo$pluie_1h_C[idx[ok]]
  val
}

df$pluie_1_2h <- extraire_pluie(df$datetime_video - 3600)
df$pluie_2_3h <- extraire_pluie(df$datetime_video - 7200)

pluie_pos <- df$pluie_1h_precedente[df$pluie_1h_precedente > 0]
q <- quantile(pluie_pos, c(.75, .90, .95, .99), na.rm = TRUE)
df$pluie <- factor(ifelse(df$pluie_1h_precedente > 0, "oui", "non"), levels = c("non", "oui"))
df$classe_pluie <- "sec"
df$classe_pluie[df$pluie_1h_precedente > 0 & df$pluie_1h_precedente < q[2]] <- "pluie_courante"
df$classe_pluie[df$pluie_1h_precedente >= q[2] & df$pluie_1h_precedente < q[3]] <- "Q90_Q95"
df$classe_pluie[df$pluie_1h_precedente >= q[3]] <- "sup_Q95"
df$classe_pluie <- factor(df$classe_pluie, levels = c("sec", "pluie_courante", "Q90_Q95", "sup_Q95"))

formule_controle <- function(source, reponse) {
  vent <- if (source == "IC") "rafale_IC_z" else "rafale_MR_z"
  direction <- if (source == "IC") c("direction_IC_sin", "direction_IC_cos") else c("direction_MR_sin", "direction_MR_cos")
  extra <- if (source == "MR") "activite_electrique" else character(0)
  meteo_vars <- if (reponse == "presence") c("temperature_z", "humidite_z", "ns(pression_z, df = 3)") else c("ns(temperature_z, df = 3)", "ns(humidite_z, df = 3)", "ns(pression_z, df = 3)")
  c(meteo_vars, vent, direction, extra, "saison", "heure", "groupe")
}

variables_controle <- function(source) {
  x <- c("temperature_z", "humidite_z", "pression_z", "saison", "heure", "groupe", "ruche_date")
  if (source == "IC") c(x, "rafale_IC_z", "direction_IC_sin", "direction_IC_cos") else c(x, "rafale_MR_z", "direction_MR_sin", "direction_MR_cos", "activite_electrique")
}

ajuster <- function(d, source, reponse, variable) {
  y <- if (reponse == "presence") "presence" else "nb_phases_WPM"
  famille <- if (reponse == "presence") binomial() else truncated_nbinom2()
  vars <- c(y, variable, variables_controle(source))
  d <- droplevels(d[complete.cases(d[, vars]), ])
  if (reponse == "intensite") d <- droplevels(d[d$nb_phases_WPM > 0, ])
  ctrl <- formule_controle(source, reponse)
  f0 <- as.formula(paste(y, "~", paste(ctrl, collapse = " + "), "+ (1 | ruche_date)"))
  f1 <- as.formula(paste(y, "~", variable, "+", paste(ctrl, collapse = " + "), "+ (1 | ruche_date)"))
  m0 <- glmmTMB(f0, family = famille, data = d)
  m1 <- glmmTMB(f1, family = famille, data = d)
  list(m0 = m0, m1 = m1, data = d)
}

coeffs <- data.frame()
tests <- data.frame()

for (version in c("complet", "sans_2202_2024")) {
  d0 <- df
  if (version == "sans_2202_2024") d0 <- d0[!(d0$ruche == "2202" & d0$annee == 2024), ]
  for (source in c("IC", "MR")) {
    for (reponse in c("presence", "intensite")) {
      for (variable in c("pluie", "classe_pluie")) {
        x <- ajuster(d0, source, reponse, variable)
        co <- summary(x$m1)$coefficients$cond
        lignes <- grep(paste0("^", variable), rownames(co))
        for (j in lignes) {
          coeffs <- rbind(coeffs, data.frame(version = version, source = source, reponse = reponse, variable = variable, terme = rownames(co)[j], ratio = exp(co[j, "Estimate"]), IC95_inf = exp(co[j, "Estimate"] - 1.96 * co[j, "Std. Error"]), IC95_sup = exp(co[j, "Estimate"] + 1.96 * co[j, "Std. Error"]), p_value = co[j, "Pr(>|z|)"]))
        }
        a0 <- anova(x$m0, x$m1)
        tests <- rbind(tests, data.frame(version = version, source = source, reponse = reponse, variable = variable, n = nrow(x$data), Chisq = a0$Chisq[2], ddl = a0$`Chi Df`[2], p_value = a0$`Pr(>Chisq)`[2]))
      }
    }
  }
}

quantite <- data.frame()
for (source in c("IC", "MR")) {
  d <- df[df$pluie_1h_precedente > 0 & df$nb_phases_WPM > 0, ]
  x <- ajuster(d, source, "intensite", "pluie_1h_precedente")
  co <- summary(x$m1)$coefficients$cond["pluie_1h_precedente", ]
  quantite <- rbind(quantite, data.frame(source = source, n = nrow(x$data), ratio = exp(co["Estimate"]), IC95_inf = exp(co["Estimate"] - 1.96 * co["Std. Error"]), IC95_sup = exp(co["Estimate"] + 1.96 * co["Std. Error"]), p_value = co["Pr(>|z|)"]))
}

lags <- data.frame()
for (source in c("IC", "MR")) {
  for (variable in c("pluie_1_2h", "pluie_2_3h")) {
    d <- df[df$nb_phases_WPM > 0, ]
    d[[variable]] <- as.integer(d[[variable]] > 0)
    x <- ajuster(d, source, "intensite", variable)
    co <- summary(x$m1)$coefficients$cond[variable, ]
    lags <- rbind(lags, data.frame(source = source, variable = variable, n = nrow(x$data), ratio = exp(co["Estimate"]), IC95_inf = exp(co["Estimate"] - 1.96 * co["Std. Error"]), IC95_sup = exp(co["Estimate"] + 1.96 * co["Std. Error"]), p_value = co["Pr(>|z|)"]))
  }
}

write.csv(data.frame(Q75 = q[1], Q90 = q[2], Q95 = q[3], Q99 = q[4], n_pluie = length(pluie_pos)), file.path(out, "quantiles_pluie.csv"), row.names = FALSE)
write.csv(coeffs, file.path(out, "coefficients_pluie.csv"), row.names = FALSE)
write.csv(tests, file.path(out, "tests_globaux_pluie.csv"), row.names = FALSE)
write.csv(quantite, file.path(out, "quantite_pluie_positive.csv"), row.names = FALSE)
write.csv(lags, file.path(out, "lags_pluie.csv"), row.names = FALSE)
