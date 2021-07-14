"""
Plot general information on the features in a given data collection.
"""

from cltoolkit.features.collection import feature_data, FeatureCollection
from clldutils.clilib import Table, add_format
import json

def register(parser):
    add_format(parser, default='pipe')
    parser.add_argument(
        '--datafile',
        help="the file storing the feature data",
        action="store",
        default="lexicore.json"
    )
    parser.add_argument(
        "--outliers",
        help="show minimal and maximal values per feature",
        action="store_true",
        default=False
    )


def run(args):
    fc = FeatureCollection.from_data(feature_data())
    data = json.load(open(args.datafile))
    keys = sorted(data.keys())

    features = {f.id: [] for f in fc.features if f.id in data[keys[0]]["features"]}
    # get outliers
    if args.outliers:
        for language in data.values():
            for feature in features:
                value = language["features"][feature]
                features[feature] += [
                        (language["dataset"], language["name"], value)]
        args.log.info("computed outliers")
        with Table(args, "Feature", "Description", "Minimum", "Maximum") as table:
            for feature in features:
                # get outliers
                fvals = sorted(features[feature], key=lambda x: x[2])
                table.append([
                    feature, fc.features[feature].name,
                    '{0[0]}-{0[1]}: {0[2]}'.format(fvals[0]),
                    '{0[0]}-{0[1]}: {0[2]}'.format(fvals[-1])
                    ])
    else:
        with Table(args, "Number", "Feature", "Description", "Type", "Note") as table:
            for i, feature in enumerate(sorted(features)):
                table.append([
                    i+1, feature, fc.features[feature].name,
                    fc.features[feature].type,
                    fc.features[feature].note])