import collections
import itertools
import pathlib

import pycldf
from cldfbench import CLDFSpec
from cldfbench import Dataset as BaseDataset
from cltoolkit import Wordlist
from cldfzenodo import oai_lexibank
from git import Repo, GitCommandError
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


def _make_cldf_collection(collection, contributions):
    langs = 0
    glottocodes = 0
    concepts = 0
    forms = 0
    for contrib in contributions:
        langs += contrib['Doculects']
        glottocodes += contrib['Glottocodes']
        concepts += contrib['Concepts']
        forms += contrib['Forms']

    return {
        'ID': collection,
        'Name': collection,
        'Description': COLLECTIONS[collection],
        'Varieties': langs,
        'Glottocodes': forms,
        'Concepts': concepts,
        'Forms': forms,
    }


def _make_cldf_lang(lang, collection):
    return {
        "ID": lang.id,
        "Name": lang.name,
        "Glottocode": lang.glottocode,
        "Dataset": lang.dataset,
        "Latitude": lang.latitude,
        "Longitude": lang.longitude,
        "Subgroup": lang.subgroup,
        "Family": lang.family,
        "Forms": len(lang.forms or []),
        "FormsWithSounds": len(lang.forms_with_sounds or []),
        "Concepts": len(lang.concepts),
        "Incollections": collection,
    }


def _code_id(feat_id, val):
    #if val is not None:
    return '{}-{}'.format(feat_id, val)
    #else:
    #       return None


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "tjukabodyobject"

    def cldf_specs(self):
        return CLDFSpec(
            metadata_fname='cldf-metadata.json',
            dir=self.cldf_dir, module="StructureDataset")

    @property
    def dataset_meta(self):
        try:
            return self._dataset_meta
        except AttributeError:
            dataset_meta = collections.OrderedDict()
            for row in self.etc_dir.read_csv('lexibank.csv', delimiter=',', dicts=True):
                if not row['Zenodo'].strip():
                    continue
                row['collections'] = set(key for key in COLLECTIONS if row.get(key, '').strip() == 'x')
                if 'ClicsCore' in row['collections']:
                    dataset_meta[row['Dataset']] = row
            self._dataset_meta = dataset_meta
            return self._dataset_meta

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

    def _datasets(self, set_=None):
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
            yield dataset

    def _schema(self, writer):
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
        writer.cldf.add_component(
            'ParameterTable',
            'Bodypart',
            'Object',
            {"name": "Feature_Spec", "datatype": "json"},
        )
        writer.cldf.add_component('CodeTable')
        t = writer.cldf.add_table(
            'collections.csv',
            'ID',
            'Name',
            'Description',
            {'name': 'Varieties', 'datatype': 'integer'},
            {'name': 'Glottocodes', 'datatype': 'integer'},
            {'name': 'Concepts', 'datatype': 'integer'},
            {'name': 'Forms', 'datatype': 'integer'},
        )
        t.tableSchema.primaryKey = ['ID']
        writer.cldf.add_component(
            'ContributionTable',
            {'name': 'Collection_IDs', 'separator': ' '},
            {'name': 'Glottocodes', 'datatype': 'integer'},
            {'name': 'Doculects', 'datatype': 'integer'},
            {'name': 'Concepts', 'datatype': 'integer'},
            {'name': 'Senses', 'datatype': 'integer'},
            {'name': 'Forms', 'datatype': 'integer'},
        )
        writer.cldf.add_foreign_key('ContributionTable', 'Collection_IDs', 'collections.csv', 'ID')

    def cmd_makecldf(self, args):
        # Read data

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

        condition = CONDITIONS["ClicsCore"]  # lambda l: len(l.concepts) >= 250
        collection = 'ClicsCore'

        the_concepts_we_want = set(itertools.chain(bodyparts, objects))

        forms_by_concept = collections.defaultdict(set)
        languages = []
        contributions = []

        for dataset in self._datasets('ClicsCore'):
            wordlist = Wordlist(datasets=[dataset])
            dataset_id = wordlist.datasets[0].metadata_dict['rdf:ID']

            contributions.append({
                'ID': dataset_id,
                'Name': dataset.properties['dc:title'],
                'Citation': dataset.properties['dc:bibliographicCitation'],
                'Collection_IDs': [collection],
                'Glottocodes': len({
                    l.glottocode
                    for l in wordlist.languages
                    if l.glottocode}),
                'Doculects': len(wordlist.languages),
                'Concepts': len(wordlist.concepts),
                'Senses': len(wordlist.senses),
                'Forms': len(wordlist.forms),
            })

            def _valid_language(lang):
                if not lang.name or lang.name == 'None':
                    args.log.warning('{0.dataset}: {0.id}: {0.name}'.format(lang))
                    return False
                elif not lang.latitude or not condition(lang):
                    return False
                else:
                    return True

            ds_languages = [
                l for l in wordlist.languages if _valid_language(l)]

            for lang in ds_languages:
                for form in lang.forms:
                    if form.concept and form.concept.concepticon_gloss in the_concepts_we_want:
                        forms_by_concept[lang.id, form.concept.concepticon_gloss].add(form.form)

            languages.extend(
                _make_cldf_lang(lang, collection)
                for lang in ds_languages)

        cldf_colls = [_make_cldf_collection(collection, contributions)]

        # Process data

        colexifications = collections.defaultdict(set)
        for (lang_id, gloss), _forms in forms_by_concept.items():
            for form in _forms:
                colexifications[lang_id, form].add(gloss)

        colex_counter = collections.Counter(
            (bodyp, obj)
            for glosses in colexifications.values()
            for bodyp in glosses
            for obj in glosses
            if bodyp in bodyparts and obj in objects)

        # TODO maybe adding concepticon ids to the feature table might be useful
        features = [
            {
                'ID': '{}And{}'.format(
                    slug(bodyp).capitalize(),
                    slug(obj).capitalize()),
                'Name': 'Colexification of {} and {}'.format(bodyp, obj),
                'Description':
                    'Computes if the concepts {} and {} are expressed'
                    ' with the same form in a language'
                    ' (i.e. they are colexified)'.format(bodyp, obj),
                'Bodypart': bodyp,
                'Object': obj,
            }
            for (bodyp, obj), _ in colex_counter.most_common(100)]

        codes = [
            {
                'ID': _code_id(f['ID'], val),
                'Parameter_ID': f['ID'],
                'Name': desc,
                'Description': "",
            }
            for f in features
            for val, desc in (
                ('True', 'colexifies {} and {}'.format(f['Bodypart'], f['Object'])),
                ('False', 'does not colexify {} and {}'.format(f['Bodypart'],
                    f['Object'])),
                ('None', "missing value"))]

        def _colex_value(lang_id, bodyp, obj):
            if not forms_by_concept[lang_id, bodyp] or not forms_by_concept[lang_id, obj]:
                return None
            elif forms_by_concept[lang_id, bodyp] & forms_by_concept[lang_id, obj]:
                return 'True'
            else:
                return 'False'
        values = [
            {
                'ID': '{}-{}'.format(lang['ID'], feat['ID']),
                'Language_ID': lang['ID'],
                'Parameter_ID': feat['ID'],
                'Value': _colex_value(lang['ID'], feat['Bodypart'], feat['Object']),
                'Code_ID': _code_id(
                    feat['ID'],
                    _colex_value(lang['ID'], feat['Bodypart'], feat['Object'])),
            }
            for lang in languages
            for feat in features]


        code_values = {code['ID']: code['Name'] for code in codes}

        languages_with_data = collections.Counter(
            val['Language_ID']
            for val in values
            if val.get('Value', "missing data") != "missing data")
        languages = [
            lang
            for lang in languages
            if languages_with_data.get(lang['ID'], 0) >= 20]
        values = [
            val
            for val in values
            if languages_with_data.get(val['Language_ID'], 0) >= 20]
        print(len(values))

        # Write CLDF data

        self._schema(args.writer)

        features.sort(key=lambda f: f['ID'])
        codes.sort(key=lambda c: c['ID'])
        languages.sort(key=lambda l: l['ID'])
        values.sort(key=lambda v: v['ID'])

        args.writer.objects['ParameterTable'] = features
        args.writer.objects['CodeTable'] = codes
        args.writer.objects['LanguageTable'] = languages
        args.writer.objects['ValueTable'] = values
        args.writer.objects['ContributionTable'] = contributions
        args.writer.objects['collections.csv'] = cldf_colls
