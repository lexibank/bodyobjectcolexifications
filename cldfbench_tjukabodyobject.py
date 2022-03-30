import pathlib
import zipfile
import collections

import pycldf
from cldfbench import CLDFSpec
from cldfbench import Dataset as BaseDataset
from cltoolkit import Wordlist
from cltoolkit.features import FeatureCollection, Feature
from cltoolkit.features.lexicon import Colexification
from cldfzenodo import oai_lexibank
from git import Repo, GitCommandError
from tqdm import tqdm
from csvw.dsv import reader
from csvw.utils import slug

COLLECTIONS = {
    'ClicsCore': (
        'Wordlists with large form inventories in which at least 250 concepts can be linked to '
        'the Concepticon',
        'large wordlists with at least 250 concepts'),
}
CONDITIONS = {
    "ClicsCore": lambda x: len(x.concepts) >= 250,
}
CLTS_2_1 = (
    "https://zenodo.org/record/4705149/files/cldf-clts/clts-v2.1.0.zip?download=1",
    'cldf-clts-clts-04f04e3')
_loaded = {}


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "tjukabodyobject"

    def cldf_specs(self):
        return CLDFSpec(
            metadata_fname='lexicon-metadata.json',
            data_fnames=dict(
                ParameterTable='lexicon-features.csv',
                ValueTable='lexicon-values.csv',
                CodeTable='lexicon-codes.csv',
            ),
            dir=self.cldf_dir, module="StructureDataset")

    @property
    def dataset_meta(self):
        res = collections.OrderedDict()
        for row in self.etc_dir.read_csv('lexibank.csv', delimiter=',', dicts=True):
            if not row['Zenodo'].strip():
                continue
            row['collections'] = set(key for key in COLLECTIONS if row.get(key, '').strip() == 'x')
            if 'ClicsCore' in row['collections']:
                res[row['Dataset']] = row
        return res

    def cmd_download(self, args):
        github_info = {rec.doi: rec.github_repos for rec in oai_lexibank()}

        for dataset, row in self.dataset_meta.items():
            ghinfo = github_info[row['Zenodo']]
            args.log.info("Checking {}".format(dataset))
            dest = self.raw_dir / dataset

            # download data
            if dest.exists():
                args.log.info("... dataset already exists.  pulling changes.")
                for remote in Repo(str(dest)).remotes:
                    remote.fetch()
            else:
                args.log.info("... cloning {}".format(dataset))
                try:
                    Repo.clone_from(ghinfo.clone_url, str(dest))
                except GitCommandError as e:
                    args.log.error("... download failed\n{}".format(str(e)))
                    continue

            # check out release (fall back to master branch)
            repo = Repo(str(dest))
            if ghinfo.tag:
                args.log.info('... checking out tag {}'.format(ghinfo.tag))
                repo.git.checkout(ghinfo.tag)
            else:
                args.log.warning('... could not determine tag to check out')
                args.log.info('... checking out master')
                try:
                    branch = repo.branches.main
                    branch.checkout()
                except AttributeError:
                    try:
                        branch = repo.branches.master
                        branch.checkout()
                    except AttributeError:
                        args.log.error('found neither main nor master branch')
                repo.git.merge()

        with self.raw_dir.temp_download(CLTS_2_1[0], 'ds.zip', log=args.log) as zipp:
            zipfile.ZipFile(str(zipp)).extractall(self.raw_dir)

    def _datasets(self, set_=None, with_metadata=False):
        """
        Load all datasets from a defined group of datasets.
        """
        if set_:
            dataset_ids = [
                dataset_id
                for dataset_id, md in self.dataset_meta.items()
                if set_ in md['collections']]
        else:
            dataset_ids = list(self.dataset_meta)

        # avoid duplicates
        dataset_ids = sorted(set(dataset_ids))

        for dataset_id in dataset_ids:
            dataset = pycldf.Dataset.from_metadata(
                self.raw_dir / dataset_id / "cldf" / "cldf-metadata.json")
            metadata = self.dataset_meta[dataset_id]
            yield (dataset, metadata) if with_metadata else dataset

    def _schema(self, writer, with_stats=False, collstats=None):
        writer.cldf.add_component(
            'LanguageTable',
            {
                'name': 'Dataset',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference',
            },
            {'name': 'Forms', 'datatype': 'integer', 'dc:description': 'Number of forms'},
            {'name': "FormsWithSounds", "datatype": "integer",
                "dc:description": "Number of forms with sounds"},
            {'name': 'Concepts', 'datatype': 'integer', 'dc:description': 'Number of concepts'},
            {'name': 'Incollections'},
            'Subgroup',
            'Family')
        t = writer.cldf.add_table(
            'collections.csv',
            'ID',
            'Name',
            'Description',
            'Varieties',
            'Glottocodes',
            'Concepts',
            'Forms',
        )
        t.tableSchema.primaryKey = ['ID']
        writer.cldf.add_component(
            'ContributionTable',
            {'name': 'Collection_IDs', 'separator': ' '},
            'Glottocodes',
            'Doculects',
            'Concepts',
            'Senses',
            'Forms',
        )
        writer.cldf.add_foreign_key('ContributionTable', 'Collection_IDs', 'collections.csv', 'ID')

        if not with_stats:
            return
        for ds, md in tqdm(self._datasets(with_metadata=True), desc='Computing summary stats'):
            langs = list(ds.iter_rows('LanguageTable', 'glottocode'))
            gcs = set(lg['glottocode'] for lg in langs if lg['glottocode'])
            senses = list(ds.iter_rows('ParameterTable', 'concepticonReference'))
            csids = set(sense['concepticonReference'] for sense in senses if sense['concepticonReference'])
            contrib = dict(
                ID=md['ID'],
                Name=ds.properties['dc:title'],
                Citation=ds.properties['dc:bibliographicCitation'],
                Collection_IDs=[key for key in COLLECTIONS if md.get(key, '').strip() == 'x'],
                Glottocodes=len(gcs),
                Doculects=len(langs),
                Concepts=len(csids),
                Senses=len(senses),
                Forms=len(list(ds['FormTable'])),
            )
            writer.objects['ContributionTable'].append(contrib)
        if collstats:
            for d in collstats.values():
                d['Glottocodes'] = len(d['Glottocodes'])
                d['Concepts'] = len(d['Concepts'])
                writer.objects['collections.csv'].append(d)

    def _colexification_features(self):
        concept_list = self.etc_dir.read_csv(
            'Tjuka-2022-784.tsv', dicts=True, delimiter='\t')
        bodyparts = [
            row['CONCEPTICON_GLOSS']
            for row in concept_list
            if row['GROUP'] == 'body']
        objects = [
            row['CONCEPTICON_GLOSS']
            for row in concept_list
            if row['GROUP'] == 'object']
        return FeatureCollection(
            Feature(
                id='{}And{}'.format(
                    slug(bodypart).capitalize(),
                    slug(obj).capitalize()),
                name="colexification of {} and {}".format(bodypart, obj),
                function=Colexification(bodypart, obj))
            for bodypart in bodyparts
            for obj in objects)

    def cmd_makecldf(self, args):
        dsinfo = {
            row["ID"]: row
            for row in reader(
                self.etc_dir / 'lexibank.csv', dicts=True, delimiter=",")}
        visited = set()
        collstats = collections.OrderedDict()
        for cid, (desc, name) in COLLECTIONS.items():
            collstats[cid] = dict(
                ID=cid,
                Name=name,
                Description=desc,
                Varieties=0,
                Glottocodes=set(),
                Concepts=set(),
                Forms=0,
            )
        languages = collections.OrderedDict()

        def _add_features(writer, features):
            for feature in features:
                writer.objects['ParameterTable'].append(dict(
                    ID=feature.id,
                    Name=feature.name,
                    Description=feature.doc,
                    Feature_Spec=feature.to_json(),
                ))
                if feature.categories:
                    for k, v in feature.categories.items():
                        writer.objects['CodeTable'].append(dict(
                            Parameter_ID=feature.id,
                            ID='{}-{}'.format(feature.id, k),
                            Name=v,
                        ))

        features_found = set()

        def _add_language(
            writer, language, features, attr_features,
            collection='', visited=set()
        ):
            l = languages.get(language.id)
            if not l:
                l = {
                    "ID": language.id,
                    "Name": language.name,
                    "Glottocode": language.glottocode,
                    "Dataset": language.dataset,
                    "Latitude": language.latitude,
                    "Longitude": language.longitude,
                    "Subgroup": language.subgroup,
                    "Family": language.family,
                    "Forms": len(language.forms or []),
                    "FormsWithSounds": len(language.forms_with_sounds or []),
                    "Concepts": len(language.concepts),
                    "Incollections": collection,
                }
            else:
                l['Incollections'] = l['Incollections'] + collection
            if language.id not in visited:
                cid = 'ClicsCore'
                try:
                    if dsinfo[language.dataset][cid] == 'x' and CONDITIONS[cid](language):
                        collstats[cid]["Glottocodes"].add(language.glottocode)
                        collstats[cid]["Varieties"] += 1
                        collstats[cid]["Forms"] += len(language.forms)
                        collstats[cid]["Concepts"].update(
                            [concept.id for concept in language.concepts])
                except:
                    print("problems with {0}".format(language.dataset))
                visited.add(language.id)
            languages[language.id] = l
            writer.objects['LanguageTable'].append(l)
            for attr in attr_features:
                writer.objects['ValueTable'].append(dict(
                    ID='{}-{}'.format(language.id, attr),
                    Language_ID=language.id,
                    Parameter_ID=attr,
                    Value=len(getattr(language, attr))
                ))
            for feature in features:
                v = feature(language)
                if not v:
                    continue
                features_found.add(feature.id)
                if feature.categories:
                    assert v in feature.categories, '{}: "{}"'.format(feature.id, v)
                writer.objects['ValueTable'].append(dict(
                    ID='{}-{}'.format(language.id, feature.id),
                    Language_ID=language.id,
                    Parameter_ID=feature.id,
                    Value=v,
                    Code_ID='{}-{}'.format(feature.id, v) if feature.categories else None,
                ))

        def _add_languages(
            writer, wordlist, condition, features,
            attr_features, collection='', visited=set([]),
        ):
            for language in tqdm(wordlist.languages, desc='computing features'):
                if language.name is None or language.name == "None":
                    args.log.warning('{0.dataset}: {0.id}: {0.name}'.format(language))
                    continue
                if language.latitude and condition(language):
                    _add_language(
                        writer, language, features, attr_features,
                        collection=collection, visited=visited)
                    yield language

        with self.cldf_writer(args) as writer:
            self._schema(writer)
            writer.cldf.add_columns(
                'ParameterTable',
                {"name": "Feature_Spec", "datatype": "json"},
            )
            features = self._colexification_features()

            for fid, fname, fdesc in [
                ('concepts', 'Number of concepts', 'Number of senses linked to Concepticon'),
                ('forms', 'Number of forms', ''),
                ('senses', 'Number of senses', ''),
            ]:
                writer.objects['ParameterTable'].append(
                    dict(ID=fid, Name=fname, Description=fdesc))

            for dataset in self._datasets('ClicsCore'):
                _ = list(_add_languages(
                    writer,
                    Wordlist(datasets=[dataset]),
                    CONDITIONS["ClicsCore"],  # lambda l: len(l.concepts) >= 250,
                    features,
                    ['concepts', 'forms', 'senses'],
                    collection='ClicsCore',
                    visited=visited,
                ))
            _add_features(
                writer,
                (f for f in features if f.id in features_found))
