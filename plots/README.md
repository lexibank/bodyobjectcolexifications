# Plotting Maps

The maps are created with the help of the [cldfviz](https://github.com/cldf/cldfviz) package. Detailed instructions on how to plot with CLDFviz can be found here: [https://github.com/cldf/cldfviz](https://github.com/cldf/cldfviz). Note that the package requires the installation of dependencies such as [cartopy](https://scitools.org.uk/cartopy/) and [matplotlib](https://maplotlib.org). Different examples of plots are presented in the [lexibank-analysed repository](https://github.com/lexibank/lexibank-analysed): [https://github.com/lexibank/lexibank-analysed/blob/main/plots/README.md](https://github.com/lexibank/lexibank-analysed/blob/main/plots/README.md).

For the study on body-object colexifications, we plotted JPGs in print quality for the article and HTML files for an interactive exploration of the data. 

All maps can be automatically created by using the Shell `Makefile` which includes the commands `plot-jpg`, `plot-html`, and `plot-family-map`. To use the `Makefile`, type `make plot-jpg` in the command line. Note that you have to be in the folder `lexibank/tjukabodyobject`. The maps will be saved in the folder `lexibank/tjukabodyobject/plots`.

If you would like to plot individual maps, you can use the following commands.

For JPG:
```shell
cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3","None":"#808080"}' --format jpg --width 20 --height 10 --dpi 300 --pacific-centered --markersize=20 --parameters=SkinAndBark --output=plots/SkinAndBark --zorder='{"True": 6, "False": 5, "None": 4}'
```

For HTML:
```shell
cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=SkinAndBark --output=plots/SkinAndBark --missing-value="#808080" --with-layers
```

For Family-Map:
```shell
cldfbench cldfviz.map cldf/cldf-metadata.json --language-properties-colormaps=tol --language-properties=Family --format html --pacific-centered --markersize=15 --output=plots/family-map
```
