library(glmmTMB)
library(mgcv)
library(DHARMa)

df <- read.csv(file.path("Données", "dataset_videos_meteo.csv"), sep = ";")
out <- file.path("Resultats", "analyse_temporelle")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

df$datetime_video <- as.POSIXct(df$datetime_video)
df <- df[df$statut %in% c("reussite", "reussite_sans_phase"), ]
df$ruche <- gsub("nap-mag1255", "", df$ruche)
df$annee <- as.numeric(format(df$datetime_video, "%Y"))
df$mois <- as.numeric(format(df$datetime_video, "%m"))
df$heure_num <- as.numeric(format(df$datetime_video, "%H"))
df$date <- as.Date(df$datetime_video)
df$jour_annee <- as.numeric(format(df$datetime_video, "%j"))
df$presence <- as.integer(df$nb_phases_WPM > 0)
df$saison <- ifelse(df$mois %in% 3:5, "printemps", ifelse(df$mois %in% 6:8, "ete", ifelse(df$mois %in% 9:11, "automne", "hiver")))
df$saison <- factor(df$saison)
df$heure <- factor(df$heure_num)
df$ruche_date <- interaction(df$ruche, df$date, drop = TRUE)

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

d <- df[df$heure_num >= 9 & df$heure_num <= 20 & !is.na(df$groupe), ]

m_presence <- glmmTMB(presence ~ groupe + saison + heure + (1 | ruche_date), family = binomial(), data = d)
m_intensite <- glmmTMB(nb_phases_WPM ~ groupe + saison + heure + (1 | ruche_date), family = truncated_nbinom2(), data = d[d$nb_phases_WPM > 0, ])

lrt <- function(m, terme) {
  m0 <- update(m, as.formula(paste(". ~ . -", terme)))
  a <- anova(m0, m)
  data.frame(terme = terme, Chisq = a$Chisq[2], ddl = a$`Chi Df`[2], p_value = a$`Pr(>Chisq)`[2])
}

tests <- rbind(
  cbind(reponse = "presence", lrt(m_presence, "groupe")),
  cbind(reponse = "presence", lrt(m_presence, "saison")),
  cbind(reponse = "presence", lrt(m_presence, "heure")),
  cbind(reponse = "intensite", lrt(m_intensite, "groupe")),
  cbind(reponse = "intensite", lrt(m_intensite, "saison")),
  cbind(reponse = "intensite", lrt(m_intensite, "heure"))
)
write.csv(tests, file.path(out, "tests_glmm_temporels.csv"), row.names = FALSE)

series <- unique(d[, c("ruche", "annee")])
res_saison <- data.frame()
for (i in seq_len(nrow(series))) {
  x <- d[d$ruche == series$ruche[i] & d$annee == series$annee[i] & d$nb_phases_WPM > 0, ]
  if (nrow(x) < 40 || length(unique(x$date)) < 12 || length(unique(x$heure_num)) < 5 || diff(range(x$jour_annee)) < 30) next
  formule <- if (length(unique(x$groupe)) > 1) nb_phases_WPM ~ s(jour_annee, k = 10) + s(heure_num, k = 5) + groupe + s(ruche_date, bs = "re") else nb_phases_WPM ~ s(jour_annee, k = 10) + s(heure_num, k = 5) + s(ruche_date, bs = "re")
  m <- gam(formule, family = nb(), data = droplevels(x), method = "REML")
  s <- summary(m)
  ligne <- data.frame(ruche = series$ruche[i], annee = series$annee[i], n = nrow(x), p_saison = s$s.table[1, "p-value"], deviance_expliquee = 100 * s$dev.expl)
  res_saison <- rbind(res_saison, ligne)
  saveRDS(m, file.path(out, paste0("gam_saison_", series$ruche[i], "_", series$annee[i], ".rds")))
}
write.csv(res_saison, file.path(out, "gam_saisonniers.csv"), row.names = FALSE)

res_groupes <- data.frame()
for (g in levels(d$groupe)) {
  x <- d[d$groupe == g & d$nb_phases_WPM > 0, ]
  if (nrow(x) < 40 || length(unique(x$heure_num)) < 5) next
  m <- gam(nb_phases_WPM ~ s(heure_num, k = 5) + s(ruche_date, bs = "re"), family = nb(), data = droplevels(x), method = "REML")
  s <- summary(m)
  res_groupes <- rbind(res_groupes, data.frame(groupe = g, n = nrow(x), p_heure = s$s.table[1, "p-value"], deviance_expliquee = 100 * s$dev.expl))
}
write.csv(res_groupes, file.path(out, "gam_intra_journaliers.csv"), row.names = FALSE)

r1 <- simulateResiduals(m_presence, n = 500)
r2 <- simulateResiduals(m_intensite, n = 500)
diag <- data.frame(modele = c("presence", "intensite"), dispersion = c(testDispersion(r1)$statistic, testDispersion(r2)$statistic), p_dispersion = c(testDispersion(r1)$p.value, testDispersion(r2)$p.value), p_uniformite = c(testUniformity(r1)$p.value, testUniformity(r2)$p.value))
write.csv(diag, file.path(out, "diagnostics_glmm_temporels.csv"), row.names = FALSE)
