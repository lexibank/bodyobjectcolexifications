
#### Load packages
library(readr)
library(dplyr)
library(ggplot2)

#### Import data tables (please change the path to the repository accordingly)

values <- read_csv("./lexibank/bodyobjectcolexifications/cldf/values.csv")
languages <- read_csv("./lexibank/bodyobjectcolexifications/cldf/languages.csv")
features <- read_csv("./lexibank/bodyobjectcolexifications/cldf/parameters.csv")


#### Include only distinct language names and delete bookkeeping languages

lang_distinct = languages[!duplicated(languages[,"Name"]),]

languages2 = lang_distinct[!(lang_distinct$Family=="Bookkeeping"),]


#### Merge Glottocodes and information on language family into `values` 

df1 = merge(values, languages2[,c("Glottocode","Family","Name","ID")], by.x='Language_ID', by.y='ID')


#### Number of unique language varieties

lang_no = length(unique(df1$Name))


#### Number of language families and their number of languages for which data is available

fam_no = length(unique(df1$Family))

fam_list = data.frame(table(languages2$Family))


#### Colexifications with at least one TRUE value

features_true = df1[df1$Value=="True",]

features_true_unique = length(unique(features_true$Code_ID))


#### Frequencies of individual colexifications based on unique languages

freq_colexi = data.frame(table(df1$Code_ID))


#### Number of object concepts that colexify with a body concept

body_list = data.frame(table(features$Bodypart))


#### Frequencies of colexifications in a given language family

distinct_df = features_true %>% distinct(Family, Code_ID, .keep_all = TRUE)

fam_freq_colexi = data.frame(table(distinct_df$Family))


#### Plot frequencies of colexification in a given language family

png(file="Desktop/family-plot.png",
    width=6, height=10, units="in", res=300)
ggplot(fam_freq_colexi, aes(Freq,reorder(Var1, Freq))) +
  geom_point(aes(size=Freq,color=Freq)) + 
  scale_x_continuous("Body-object colexifications in total") + 
  scale_y_discrete("Language family") +
  theme_minimal() +   
  scale_colour_gradient(low = "blue", high="orange", name="Color") +
  guides(size=guide_legend(title="Size")) 
dev.off()
