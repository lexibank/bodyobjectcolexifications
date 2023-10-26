# R version 4.3.1
# Script created on October 25, 2023

# Define version and load packages
library(groundhog)  # Version 3.1.2
pkgs = c("brms","posterior", "ggplot2", "dplyr", "tidyr", "reshape2")
groundhog.library(pkgs, "2023-10-01")


# Load data
# The body-object colexifications were extracted from the GitHub repository of the study: https://github.com/lexibank/bodyobjectcolexifications/blob/main/cldf/values.csv
# For the ratings on visual and haptic perception, I used the Lancaster Sensorimotor Norms (Lynott et al. 2020) 
# that were mapped to the Concepticon concept sets and added to the NoRaRe database (Tjuka et al. 2023). 
# The data can be downloaded here: https://github.com/concepticon/norare-data/blob/v1.0.1/datasets/Lynott-2020-Sensorimotor/Lynott-2020-Sensorimotor.tsv
# The tables were merged and the resulting file is available in the GitHub repository: 
data = read.delim("perception-vision-touch.tsv", header=TRUE, sep="\t")

# Calculate mean values for body and object concepts for vision and touch
mean(data$VISUAL_BODY)
mean(data$VISUAL_OBJECT)
mean(data$HAPTIC_BODY)
mean(data$HAPTIC_OBJECT)

# Correlate ratings for vision and touch across body and object concepts
cor.test(data$VISUAL_BODY,data$VISUAL_OBJECT,method = "pearson")
cor.test(data$HAPTIC_BODY,data$HAPTIC_OBJECT,method = "pearson")

# Transform the data so that perception type (vision and touch) is listed in a separate column
data_tf = melt(data, id.vars = c("BODY", "OBJECT"), measure.vars = c("VISUAL_BODY", "VISUAL_OBJECT", "HAPTIC_BODY", "HAPTIC_OBJECT"))
data_tf$perception_type = ifelse(grepl("VISUAL", data_tf$variable), "vision", "touch")

# Define the Bayesian linear regression model with varying residuals for perception type 
# and an interaction between body and object concepts
model = brm(
  value ~ perception_type * BODY * OBJECT + (1 | perception_type),
  data = data_tf,
  family = gaussian(),
  prior = c(set_prior("normal(0, 5)", class = "Intercept"),
            set_prior("cauchy(0, 2)", class = "sd"),
            set_prior("cauchy(0, 2)", class = "sd", group = "perception_type")),
  iter = 2000,  # I used a low number of iterations to decrease the processing time
  chains = 4 
)

# Summarize the model
summary = summary(model)

# Extract the samples of the posterior distribution and convert to data frame
post_samples = as.data.frame(as_draws_array(model))

# Inspect the data frame 
head(post_samples)
summary(post_samples)
str(post_samples)

# Define the columns for the vision and touch residuals
vision = grep("r_perception_type\\[vision,Intercept\\]", colnames(post_samples))
touch = grep("r_perception_type\\[touch,Intercept\\]", colnames(post_samples))

# Compute standard deviations for the residuals of vision and touch
sd_vision = sd(as.vector(unlist(post_samples[, vision])))
sd_touch = sd(as.vector(unlist(post_samples[, touch])))
cat("Standard Deviation for Vision Residuals:", sd_vision, "\n")
cat("Standard Deviation for Touch Residuals:", sd_touch, "\n")


### Visualize the results

# Define a colorblind friendly color palette
colors = c("#009E73", "#E69F00")

# Calculate mean values for vision and touch for each body-object colexification
interaction_means <- aggregate(value ~ perception_type + BODY + OBJECT, data_tf, mean)

# Define groups of unique body concepts
unique_body <- unique(interaction_means$BODY)

# Loop through unique body concepts and create individual plots
for (body_concept in unique_body) {
  body <- subset(interaction_means, BODY == body_concept)
  p <- ggplot(body, aes(x = OBJECT, y = value, color = perception_type, group = perception_type)) +
    geom_line(size = 1.5) +
    labs(x = "Object Concept", y = "Mean Ratings", color = "Perception Type") +
    scale_color_manual(values = colors) +
    theme_minimal(base_size = 14) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    theme(plot.background = element_rect(fill = "white"), panel.background = element_rect(fill = "white", color = "white")) +
    ggtitle(paste("Body Concept:", body_concept)) +
    ylim(0, 5)
  ggsave(paste("plot_", gsub(" ", "", body_concept), ".png"), plot = p, width = 8, height = 6, dpi = 300)
}

