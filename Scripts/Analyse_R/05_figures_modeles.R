library(ggplot2)

base <- file.path("Resultats", "modeles_meteo")
out <- file.path("Resultats", "figures_modeles")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

co <- read.csv(file.path(base, "coefficients_modeles.csv"))
co$reponse <- ifelse(grepl("^presence", co$modele), "Présence", "Intensité")
co$source <- ifelse(grepl("_IC_", co$modele), "IC", "MR")
co$vent <- ifelse(grepl("_rafale_", co$modele), "Rafale maximale", "Vent moyen")
co$version <- ifelse(grepl("sans_2202_2024", co$modele), "sans_2202_2024", "complet")

garder <- c("temperature_moy_30min_z", "humidite_moy_30min_z", "pression_moy_30min_z", "rafales_IC_max_30min_z", "rafales_MR_max_30min_z")
d <- co[co$version == "complet" & co$vent == "Rafale maximale" & co$terme %in% garder, ]
d$variable <- ifelse(grepl("temperature", d$terme), "Température", ifelse(grepl("humidite", d$terme), "Humidité", ifelse(grepl("pression", d$terme), "Pression", "Rafale maximale")))

p <- ggplot(d, aes(ratio, variable, colour = source)) + geom_vline(xintercept = 1, linetype = 2) + geom_point(position = position_dodge(.4)) + geom_errorbarh(aes(xmin = ratio_IC95_inf, xmax = ratio_IC95_sup), position = position_dodge(.4), height = .15) + facet_wrap(~reponse) + xlab("Rapport d'effet par augmentation d'un écart-type") + ylab(NULL) + theme_bw()
ggsave(file.path(out, "associations_lineaires.pdf"), p, width = 9, height = 4.5)

pluie <- read.csv(file.path("Resultats", "analyse_pluie", "coefficients_pluie.csv"))
pd <- pluie[pluie$version == "complet" & pluie$variable == "classe_pluie", ]
pd$reponse <- ifelse(pd$reponse == "presence", "Présence", "Intensité")
p2 <- ggplot(pd, aes(terme, ratio, colour = source)) + geom_hline(yintercept = 1, linetype = 2) + geom_point(position = position_dodge(.4)) + geom_errorbar(aes(ymin = IC95_inf, ymax = IC95_sup), position = position_dodge(.4), width = .15) + facet_wrap(~reponse, scales = "free_y") + xlab(NULL) + ylab("Rapport estimé") + theme_bw() + theme(axis.text.x = element_text(angle = 20, hjust = 1))
ggsave(file.path(out, "classes_pluie.pdf"), p2, width = 9, height = 4.5)
