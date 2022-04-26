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

        for dataset in self._datasets('ClicsCore'):
            wordlist = Wordlist(datasets=[dataset])

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
                'ID': '{}-{}'.format(f['ID'], val),
                'Parameter_ID': f['ID'],
                'Name': name,
            }
            for f in features
            for val, name in (
                ('true', 'colexifies {} and {}'.format(f['Bodypart'], f['Object'])),
                ('false', 'does not colexify {} and {}'.format(f['Bodypart'], f['Object'])),
                ('null', 'missing data'))]

        def _colex_value(lang_id, bodyp, obj):
            if not forms_by_concept[lang_id, bodyp] or not forms_by_concept[lang_id, obj]:
                return 'null'
            elif forms_by_concept[lang_id, bodyp] & forms_by_concept[lang_id, obj]:
                return 'true'
            else:
                return 'false'
        values = [
            {
                'ID': '{}-{}'.format(lang['ID'], feat['ID']),
                'Language_ID': lang['ID'],
                'Parameter_ID': feat['ID'],
                'Code_ID': '{}-{}'.format(
                    feat['ID'],
                    _colex_value(lang['ID'], feat['Bodypart'], feat['Object'])),
            }
            for lang in languages
            for feat in features]
        values = [v for v in values if not v['Code_ID'].endswith('-null')]

        languages_with_data = {
            val['Language_ID']
            for val in values
            if not val['Code_ID'].endswith('-null')}
        languages = [
            lang
            for lang in languages
            if lang['ID'] in languages_with_data]
        values = [
            val
            for val in values
            if val['Language_ID'] in languages_with_data]

        # Write CLDF data

        with self.cldf_writer(args) as writer:
            self._schema(writer)

            features.sort(key=lambda f: f['ID'])
            codes.sort(key=lambda c: c['ID'])
            languages.sort(key=lambda l: l['ID'])
            values.sort(key=lambda v: v['ID'])

            writer.objects['ParameterTable'] = features
            writer.objects['CodeTable'] = codes
            writer.objects['LanguageTable'] = languages
            writer.objects['ValueTable'] = values
