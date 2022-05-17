# Using the Body-Object-Colexification Repository

Body-Object-CLICS is a collection of colexifications between body and object concepts (for more details, see Tjuka [2022](https://calc.hypotheses.org/3840)). The CLDF dataset was compiled to establish the 100 most frequent body-object colexifications within the `ClicsCore` collection included in the [CLICS](https://clics.clld.org) database. The data is linked to [Concepticon](https://concepticon.clld.org/) and [Glottolog](https://glottolog.org/). The datasets integrated in this collection are given in [etc/lexibank.tsv](etc/lexibank.tsv).

In the following, the workflows established for this repository are described. Since this repository is based on the [Lexibank](https://github.com/lexibank) repository, further information can be found there.

## 1 Lexibank Workflow

This repository contains a `cldfbench` package, bundling

- code
  - to download the lexibank dataset and
  - to compute the body-object colexifcations from this data.

The workflow consists of a sequence of calls to `cldfbench` subcommands, which in turn call the code described above.


1. Install the package (including Dependencies)
   ```shell
   $ git clone https://github.com/lexibank/tjukabodyobject
   $ cd tjukabodyobject
   $ pip install -e .
   ```

2. Download the data collections

   The data collections will be downloaded by reading the most recent selection of lexibank datasets from the file `src/lexibank/data/lexibank.tsv` and then downloading the relevant datasets to a folder which you specify with the kewyord `destination`. We will call the folder `datasets` in the following.

   ```shell
   $ cldfbench download tjukabodyobject.py
   ```

3. Compute body-object colexifcations

   The analysis results of `tjukabodyobject` are stored in one CLDF Datasets including the 100 most frequent body-object colexifications.

   These data are created running
   ```shell
   $ cldfbench makecldf --with-cldfreadme cldfbench_tjukabodyobject.py
   ```

4. Make sure valid CLDF data has been created:
   ```shell
   pytest
   ```

## 2 Data exploration

### Metadata

In addition to body-object colexifcations, the CLDF data also contains
- provenance information, linking each doculect to the dataset from which it was extracted
- summary statistics about the collections into which we bundle the datasets.

This data is contained in the tables [contributions.csv](cldf/contributions.csv) and [collections.csv](cldf/collections.csv).
We can look at the numbers of unique Glottocodes or Concepts and the number of individual forms in each collection:
```shell
$ csvcut -c ID,Glottocodes,Concepts,Forms cldf/collections.csv | csvformat -T
ID Glottocodes Concepts Forms
ClicsCore   1950907  29064 1950907
```

`contributions.csv` also lists numbers of doculects and senses. Datasets with a low ratio between `Glottocodes` and `Doculects`, i.e. with many doculects mapped to the same glottocode, are typical dialectal collections. We can check this ratio running
```shell
$ csvsql --query "select id, name, cast(glottocodes as float) / cast(doculects as float) as ratio from contributions order by ratio limit 1" \
cldf/contributions.csv 
ID,Name,ratio
zhivlovobugrian,"CLDF Dataset derived from Zhivlov's ""Annotated Swadesh wordlists for the Ob-Ugrian group"" from 2011",0.09523809523809523
```

### Body-Object Colexifications

To check for available body-object colexifcations, you can inspect the CLDF ParameterTable of the respective
CLDF datasets:
```shell
$ csvcut -c ID,Name cldf/parameters.csv | column -s"," -t
ID                      Name
AnkleAndKnot            Colexification of ANKLE and KNOT
ArmAndBranch            Colexification of ARM and BRANCH
ArmAndValley            Colexification of ARM and VALLEY
BackAndBark             Colexification of BACK and BARK
BackAndRoof             Colexification of BACK and ROOF
BellyAndPen             Colexification of BELLY and PEN
BloodvesselAndRoot      Colexification of BLOOD VESSEL and ROOT
BloodvesselAndThread    Colexification of BLOOD VESSEL and THREAD
BodyAndLeather          Colexification of BODY and LEATHER
BodyAndShell            Colexification of BODY and SHELL
BodyAndTreetrunk        Colexification of BODY and TREE TRUNK
BoneAndBowl             Colexification of BONE and BOWL
BoneAndPlantstem        Colexification of BONE and PLANT STEM
BoneAndPlate            Colexification of BONE and PLATE
BoneAndRope             Colexification of BONE and ROPE
BoneAndShell            Colexification of BONE and SHELL
BoneAndStick            Colexification of BONE and STICK
BoneAndTree             Colexification of BONE and TREE
ButtocksAndBottom       Colexification of BUTTOCKS and BOTTOM
EarAndEarring           Colexification of EAR and EARRING
EarAndLeaf              Colexification of EAR and LEAF
ElbowAndCorner          Colexification of ELBOW and CORNER
EyeAndFire              Colexification of EYE and FIRE
EyeAndFruit             Colexification of EYE and FRUIT
EyeAndGrain             Colexification of EYE and GRAIN
EyeAndSeed              Colexification of EYE and SEED
EyeAndTree              Colexification of EYE and TREE
EyeAndWheel             Colexification of EYE and WHEEL
FaceAndEdge             Colexification of FACE and EDGE
FaceAndSide             Colexification of FACE and SIDE
FingerAndRing           Colexification of FINGER and RING
FingernailAndNailtool   Colexification of FINGERNAIL and NAIL (TOOL)
FootAndCorner           Colexification of FOOT and CORNER
FootAndWheel            Colexification of FOOT and WHEEL
ForeheadAndCape         Colexification of FOREHEAD and CAPE
ForeheadAndPan          Colexification of FOREHEAD and PAN
HairAndLeaf             Colexification of HAIR and LEAF
HairheadAndLeaf         Colexification of HAIR (HEAD) and LEAF
HandAndBranch           Colexification of HAND and BRANCH
HandAndMountain         Colexification of HAND and MOUNTAIN
HandAndValley           Colexification of HAND and VALLEY
HeadAndCape             Colexification of HEAD and CAPE
HeadAndRoof             Colexification of HEAD and ROOF
HeadAndSummit           Colexification of HEAD and SUMMIT
HeadAndTipofobject      Colexification of HEAD and TIP (OF OBJECT)
HeadAndTop              Colexification of HEAD and TOP
HeartAndFirewood        Colexification of HEART and FIREWOOD
HeelAndMortar           Colexification of HEEL and MORTAR
HipAndSide              Colexification of HIP and SIDE
IntestinesAndBed        Colexification of INTESTINES and BED
IntestinesAndSausage    Colexification of INTESTINES and SAUSAGE
LegAndBowl              Colexification of LEG and BOWL
LegAndCup               Colexification of LEG and CUP
LegAndSky               Colexification of LEG and SKY
LegAndTreetrunk         Colexification of LEG and TREE TRUNK
LipAndEdge              Colexification of LIP and EDGE
LipAndShore             Colexification of LIP and SHORE
LungAndLake             Colexification of LUNG and LAKE
MouthAndDoor            Colexification of MOUTH and DOOR
MouthAndEdge            Colexification of MOUTH and EDGE
MouthAndHole            Colexification of MOUTH and HOLE
NeckAndCollar           Colexification of NECK and COLLAR
NippleAndSeed           Colexification of NIPPLE and SEED
NoseAndArrow            Colexification of NOSE and ARROW
NoseAndCape             Colexification of NOSE and CAPE
NoseAndFlower           Colexification of NOSE and FLOWER
NoseAndTop              Colexification of NOSE and TOP
NostrilAndHole          Colexification of NOSTRIL and HOLE
PenisAndEgg             Colexification of PENIS and EGG
PenisAndSeed            Colexification of PENIS and SEED
RibAndShore             Colexification of RIB and SHORE
RibAndSide              Colexification of RIB and SIDE
ShoulderbladeAndOar     Colexification of SHOULDERBLADE and OAR
ShoulderbladeAndPaddle  Colexification of SHOULDERBLADE and PADDLE
ShoulderbladeAndSpade   Colexification of SHOULDERBLADE and SPADE
SkinAndBark             Colexification of SKIN and BARK
SkinAndBasket           Colexification of SKIN and BASKET
SkinAndBook             Colexification of SKIN and BOOK
SkinAndLeather          Colexification of SKIN and LEATHER
SkinAndLoincloth        Colexification of SKIN and LOINCLOTH
SkinAndMushroom         Colexification of SKIN and MUSHROOM
SkinAndShell            Colexification of SKIN and SHELL
SkinAndSkinoffruit      Colexification of SKIN and SKIN (OF FRUIT)
SkullAndTop             Colexification of SKULL and TOP
TemplesAndTop           Colexification of TEMPLES and TOP
TendonAndRoot           Colexification of TENDON and ROOT
TesticlesAndBall        Colexification of TESTICLES and BALL
TesticlesAndCheese      Colexification of TESTICLES and CHEESE
TesticlesAndEgg         Colexification of TESTICLES and EGG
TesticlesAndFruit       Colexification of TESTICLES and FRUIT
TesticlesAndSeed        Colexification of TESTICLES and SEED
ThroatAndCollar         Colexification of THROAT and COLLAR
ThroatAndNecklace       Colexification of THROAT and NECKLACE
TongueAndFlame          Colexification of TONGUE and FLAME
ToothAndBead            Colexification of TOOTH and BEAD
ToothAndLeaf            Colexification of TOOTH and LEAF
ToothAndSproutshoot     Colexification of TOOTH and SPROUT (SHOOT)
VeinAndRoot             Colexification of VEIN and ROOT
WaistAndBelt            Colexification of WAIST and BELT
WaistAndSpade           Colexification of WAIST and SPADE
```

## 3 Data visualization

Visual exploration of the data can be done with `cldfviz`, a `cldfbench` plugin to visualize CLDF datasets.

Let's first look at the distribution of languages in the sample on a map:
```shell
cldfbench cldfviz.map cldf/cldf-metadata.json --language-properties-colormaps=tol --language-properties=Family --format html --pacific-centered --markersize=15 --output=plots/family-map
```

This command will generate a HTML file in the `plots` folder. To explore individual body-object colexifcations, the `-parameter` value can be used:
```shell
cldfbench cldfviz.map cldf/cldf-metadata.json --colormaps '{"True":"#FF4500","False":"#BA55D3"}' --format html --pacific-centered --markersize=15 --parameters=SkinAndBark --output=plots/SkinAndBark --missing-value="#808080" --with-layers
```
Not that each body-object colexifcation has two major values, `true` and `false`, and -- as a third case -- `None`, when data are missing (there is no word for "skin" or for "bark" in our data).
