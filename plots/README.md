# Plotting Instructions

The plots are created with the help of the [cldfviz](https://github.com/cldf/cldfviz) package. Detailes instructions on how to plot with CLDFviz can be found here: [https://github.com/cldf/cldfviz](https://github.com/cldf/cldfviz) Note that the package requires the installation of dependencies such as [cartopy](https://scitools.org.uk/cartopy/) and [matplotlib](https://maplotlib.org). Different examples of plots are presented in the [lexibank-analysed repository](https://github.com/lexibank/lexibank-analysed): [https://github.com/lexibank/lexibank-analysed/blob/main/plots/README.md](https://github.com/lexibank/lexibank-analysed/blob/main/plots/README.md).

For the study on body-object colexifications, we plotted JPGs in print quality for the article and HTML files for an interactive exploration of the data. 

All plots can be automatically created by using the Shell `Makefile` which includes the commands `plot-jpg` and `plot-html`. To use the `Makefile`, type `make plot-jpg` in the command line. Note that you have to be in the folder `lexibank/tjukabodyobject`. The plots will be saved in the folder `lexibank/tjukabodyobject/plots`.
