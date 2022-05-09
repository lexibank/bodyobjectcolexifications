plot-html:
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=SkinAndBark --output=plots/SkinAndBark --missing-value="#808080" --with-layers
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=BoneAndRope --output=plots/BoneAndRope --missing-value="#808080" --with-layers
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=EyeAndSeed --output=plots/EyeAndSeed --missing-value="#808080" --with-layers
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=MouthAndDoor --output=plots/MouthAndDoor --missing-value="#808080" --with-layers

plot-jpg:
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format jpg --width 20 --height 10 --dpi 300 --pacific-centered --markersize=20 --parameters=SkinAndBark --output=plots/SkinAndBark --zorder='{"True": 6, "False": 5, "None": 4}'
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format jpg --width 20 --height 10 --dpi 300 --pacific-centered --markersize=20 --parameters=BoneAndRope --output=plots/BoneAndRope --zorder='{"True": 6, "False": 5, "None": 4}'
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format jpg --width 20 --height 10 --dpi 300 --pacific-centered --markersize=20 --parameters=EyeAndSeed --output=plots/EyeAndSeed --zorder='{"True": 6, "False": 5, "None": 4}'
	cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format jpg --width 20 --height 10 --dpi 300 --pacific-centered --markersize=20 --parameters=MouthAndDoor --output=plots/MouthAndDoor --zorder='{"True": 6, "False": 5, "None": 4}'
