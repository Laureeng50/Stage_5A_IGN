library(glmmTMB)
library(splines)

df <- read.csv(file.path("Données", "dataset_videos_meteo.csv"), sep = ";")
out <- file.path("Resultats", "nonlinearites")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

df$datetime_video <- as.POSIXct(df$datetime_video)
df <- df[df$statut %in% c("reussite", "reussite_sans_phase") & df$nb_phases_WPM > 0, ]
df$ruche <- gsub("nap-mag1255", "", df$ruche)
df$annee <- as.numeric(format(df$datetime_video, "%Y"))
df$mois <- as.numeric(format(df$datetime_video, "%m"))
df$heure_num <- as.numeric(format(df$datetime_video, "%H"))
df$date <- as.Date(df$datetime_video)
df <- df[df$heure_num >= 9 & df$heure_num <= 20, ]
df$saison <- factor(ifelse(df$mois %in% 3:5, "printemps", ifelse(df$mois %in% 6:8, "ete", "automne")))
df$heure <- factor(df$heure_num)
df$ruche_date <- interaction(df$ruche, df$date, drop = TRUE)
df$pluie <- as.integer(df$pluie_1h_precedente > 0)
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

vars <- c(temperature = "temperature_moy_30min", humidite = "humidite_moy_30min", pression = "pression_moy_30min")
centres <- sapply(vars, function(x) mean(df[[x]], na.rm = TRUE))
ecarts <- sapply(vars, function(x) sd(df[[x]], na.rm = TRUE))
for (v in names(vars)) df[[paste0(v, "_z")]] <- (df[[vars[v]]] - centres[v]) / ecarts[v]

df$vent_IC_z <- as.numeric(scale(df$vent_moyen_IC_30min))
df$rafale_IC_z <- as.numeric(scale(df$rafales_IC_max_30min))
df$vent_MR_z <- as.numeric(scale(df$vent_moyen_MR_30min))
df$rafale_MR_z <- as.numeric(scale(df$rafales_MR_max_30min))

faire_modele <- function(d, source, vent, variable = NULL, spline = FALSE, bp1 = NULL, bp2 = NULL) {
  vent_var <- if (source == "IC" && vent == "moyen") "vent_IC_z" else if (source == "IC") "rafale_IC_z" else if (vent == "moyen") "vent_MR_z" else "rafale_MR_z"
  direction <- if (source == "IC") c("direction_IC_sin", "direction_IC_cos") else c("direction_MR_sin", "direction_MR_cos")
  extra <- if (source == "MR") "activite_electrique" else character(0)
  termes <- c("temperature_z", "humidite_z", "pression_z", vent_var, direction, "pluie", "saison", "heure", "groupe", extra)
  if (!is.null(variable)) {
    z <- paste0(variable, "_z")
    if (spline) termes[termes == z] <- paste0("ns(", z, ", df = 3)")
    if (!is.null(bp1)) {
      d$h1 <- pmax(0, d[[z]] - bp1)
      termes <- c(termes, "h1")
    }
    if (!is.null(bp2)) {
      d$h2 <- pmax(0, d[[z]] - bp2)
      termes <- c(termes, "h2")
    }
  }
  f <- as.formula(paste("nb_phases_WPM ~", paste(termes, collapse = " + "), "+ (1 | ruche_date)"))
  glmmTMB(f, family = truncated_nbinom2(), data = d)
}

tests <- data.frame()
breakpoints <- data.frame()
seconds <- data.frame()

for (version in c("complet", "sans_2202_2024")) {
  d0 <- df
  if (version == "sans_2202_2024") d0 <- d0[!(d0$ruche == "2202" & d0$annee == 2024), ]
  for (source in c("IC", "MR")) {
    for (vent in c("moyen", "rafale")) {
      vent_var <- if (source == "IC" && vent == "moyen") "vent_IC_z" else if (source == "IC") "rafale_IC_z" else if (vent == "moyen") "vent_MR_z" else "rafale_MR_z"
      direction <- if (source == "IC") c("direction_IC_sin", "direction_IC_cos") else c("direction_MR_sin", "direction_MR_cos")
      extra <- if (source == "MR") "activite_electrique" else character(0)
      besoin <- c("nb_phases_WPM", "temperature_z", "humidite_z", "pression_z", vent_var, direction, "pluie", "saison", "heure", "groupe", "ruche_date", extra)
      d <- droplevels(d0[complete.cases(d0[, besoin]), ])
      nom_modele <- paste(source, vent, version, sep = "_")

      for (variable in names(vars)) {
        m0 <- faire_modele(d, source, vent)
        ms <- faire_modele(d, source, vent, variable, spline = TRUE)
        a <- anova(m0, ms)
        tests <- rbind(tests, data.frame(modele = nom_modele, variable = variable, n = nrow(d), AIC_lineaire = AIC(m0), AIC_spline = AIC(ms), delta_AIC = AIC(ms) - AIC(m0), p_LRT = a$`Pr(>Chisq)`[2]))

        z <- paste0(variable, "_z")
        valeurs <- d[[z]]
        grille <- seq(quantile(valeurs, .10), quantile(valeurs, .90), length.out = 80)
        grille <- grille[sapply(grille, function(x) sum(valeurs <= x) >= 100 && sum(valeurs > x) >= 100)]
        if (!length(grille)) next

        profils <- data.frame()
        for (bp in grille) {
          m <- tryCatch(faire_modele(d, source, vent, variable, bp1 = bp), error = function(e) NULL)
          if (!is.null(m)) profils <- rbind(profils, data.frame(bp = bp, logLik = as.numeric(logLik(m)), AIC = AIC(m) + 2))
        }
        if (!nrow(profils)) next

        best <- profils[which.min(profils$AIC), ]
        limite <- max(profils$logLik) - qchisq(.95, 1) / 2
        zone <- profils[profils$logLik >= limite, ]
        bp <- best$bp
        bp_phys <- bp * ecarts[variable] + centres[variable]
        inf_phys <- min(zone$bp) * ecarts[variable] + centres[variable]
        sup_phys <- max(zone$bp) * ecarts[variable] + centres[variable]
        retenu <- best$AIC <= AIC(m0) - 2

        breakpoints <- rbind(breakpoints, data.frame(modele = nom_modele, variable = variable, breakpoint = bp_phys, IC95_inf = inf_phys, IC95_sup = sup_phys, AIC_breakpoint = best$AIC, delta_AIC_vs_lineaire = best$AIC - AIC(m0), retenu = retenu))

        if (variable == "temperature" && retenu && best$AIC <= AIC(m0) - 4 && AIC(ms) <= best$AIC - 2) {
          candidats2 <- grille[grille > bp]
          candidats2 <- candidats2[sapply(candidats2, function(x) sum(valeurs > x) >= 50)]
          profils2 <- data.frame()
          for (bp2 in candidats2) {
            m2 <- tryCatch(faire_modele(d, source, vent, variable, bp1 = bp, bp2 = bp2), error = function(e) NULL)
            if (!is.null(m2)) profils2 <- rbind(profils2, data.frame(bp2 = bp2, AIC = AIC(m2) + 4))
          }
          if (nrow(profils2)) {
            b2 <- profils2[which.min(profils2$AIC), ]
            seconds <- rbind(seconds, data.frame(modele = nom_modele, breakpoint_1 = bp_phys, breakpoint_2 = b2$bp2 * ecarts[variable] + centres[variable], AIC_1BP = best$AIC, AIC_2BP = b2$AIC, retenu = b2$AIC <= best$AIC - 2))
          }
        }
      }
    }
  }
}

write.csv(tests, file.path(out, "tests_nonlinearite.csv"), row.names = FALSE)
write.csv(breakpoints, file.path(out, "breakpoints.csv"), row.names = FALSE)
write.csv(seconds, file.path(out, "second_breakpoint_temperature.csv"), row.names = FALSE)
