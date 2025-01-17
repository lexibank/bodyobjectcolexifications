import collections
import itertools
import pathlib
import re
import unicodedata

import pycldf
from cldfbench import CLDFSpec
from cldfbench import Dataset as BaseDataset
from cltoolkit import Wordlist
from cldfzenodo import oai_lexibank
from git import Repo, GitCommandError

COLLECTIONS = {
    'ClicsCore': (
        'Wordlists with large form inventories in which at least 250 concepts can be linked to '
        'the Concepticon',
        'large wordlists with at least 250 concepts'),
}
CONDITIONS = {
    "ClicsCore": lambda x: len(x.concepts) >= 250,
}


def slug(s):
    res = ''.join(
        c.lower()
        for c in unicodedata.normalize('NFD', s)
        if c.isascii() and c.isalnum())
    assert re.match('[A-Za-z0-9]*$', res), res
    return res


def make_cldf_collection(collection, contributions):
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


def language_id(lang):
    return lang.glottocode or lang.id


def make_cldf_lang(lang, collection):
    return {
        "ID": language_id(lang),
        "Name": lang.name,
        "Glottocode": lang.glottocode,
        "Dataset": lang.dataset,
        "Latitude": lang.latitude,
        "Longitude": lang.longitude,
        "Subgroup": lang.subgroup,
        "Family": lang.family,
        "Forms": len(lang.forms or []),
        "Concepts": len(lang.concepts),
        "Incollections": collection,
    }


def make_form(form):
    return {
        'ID': form.id,
        'Language_ID': language_id(form.language),
        'Form': form.form,
        'Concepticon_Gloss': form.concept.concepticon_gloss,
    }


def code_id(feat_id, val):
    return '{}-{}'.format(feat_id, val)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = 'tjukabodyobject'

    def cldf_specs(self):
        return CLDFSpec(
            metadata_fname='cldf-metadata.json',
            dir=self.cldf_dir, module="StructureDataset")

    def cmd_download(self, args):
        github_info_by_doi = {rec.doi: rec.github_repos for rec in oai_lexibank()}
        dataset_list = self.etc_dir.read_csv(
            'datasets.tsv', delimiter='\t', dicts=True)

        for row in dataset_list:
            dataset_id = row['ID']
            doi = row['Zenodo']
            github_org = row['Organisation']
            github_repo = row['Repository']
            clone_url = 'https://github.com/{}/{}'.format(
                github_org, github_repo)
            if row.get('Zenodo'):
                tag = github_info_by_doi[doi].tag
            else:
                tag = None
            args.log.info("Checking {}".format(dataset_id))
            dest = self.raw_dir / dataset_id

            # download data
            if dest.exists():
                args.log.info("... dataset already exists.  pulling changes.")
                for remote in Repo(str(dest)).remotes:
                    remote.fetch()
            else:
                args.log.info("... cloning {}".format(dataset_id))
                try:
                    Repo.clone_from(clone_url, str(dest))
                except GitCommandError as e:
                    args.log.error("... download failed\n{}".format(str(e)))
                    continue

            # check out release (fall back to master branch)
            repo = Repo(str(dest))
            if tag:
                args.log.info('... checking out tag {}'.format(tag))
                repo.git.checkout(tag)
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

    def _schema(self, writer):
        writer.cldf.add_component(
            'LanguageTable',
            {
                'name': 'Dataset',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#contributionReference',
            },
            {'name': 'Forms', 'datatype': 'integer', 'dc:description': 'Number of forms'},
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
        writer.cldf.add_component('ExampleTable')
        writer.cldf.add_foreign_key('ContributionTable', 'Collection_IDs', 'collections.csv', 'ID')
        writer.cldf.add_columns(
            'ValueTable',
            {
                'name': 'Example_IDs',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#exampleReference',
                'separator': ';',
            },
        )

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

        form_counts = {}
        forms_by_language = collections.defaultdict(list)
        languages = collections.OrderedDict()
        contributions = []

        dataset_list = self.etc_dir.read_csv(
            'datasets.tsv', delimiter='\t', dicts=True)

        for dataset_info in dataset_list:
            dataset_id = dataset_info['ID']
            dataset = pycldf.Dataset.from_metadata(
                self.raw_dir / dataset_id / "cldf" / "cldf-metadata.json")
            wordlist = Wordlist(datasets=[dataset])

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

            def _valid_form(form):
                return form.concept and form.concept.concepticon_gloss in the_concepts_we_want

            ds_languages = []
            for lang in wordlist.languages:
                if not _valid_language(lang):
                    continue
                lang_forms = [
                    make_form(f) for f in lang.forms if _valid_form(f)]
                if lang.glottocode and len(lang_forms) < form_counts.get(lang.glottocode, 0):
                    continue
                ds_languages.append(lang)
                forms_by_language[language_id(lang)] = lang_forms
                if lang.glottocode:
                    form_counts[lang.glottocode] = len(lang_forms)

            languages.update(
                (language_id(lang), make_cldf_lang(lang, collection))
                for lang in ds_languages)

        cldf_colls = [make_cldf_collection(collection, contributions)]

        # Process data

        forms_by_concept = collections.defaultdict(set)
        for lang_forms in forms_by_language.values():
            for form in lang_forms:
                lang_id = form['Language_ID']
                gloss = form['Concepticon_Gloss']
                forms_by_concept[lang_id, gloss].add(form['Form'])

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
                'ID': code_id(f['ID'], val),
                'Parameter_ID': f['ID'],
                'Name': desc,
            }
            for f in features
            for val, desc in (
                ('True', 'colexifies {} and {}'.format(
                    f['Bodypart'], f['Object'])),
                ('False', 'does not colexify {} and {}'.format(
                    f['Bodypart'], f['Object'])),
                ('None', "missing value"))]

        def _colex_value(lang_id, bodyp, obj):
            if not forms_by_concept[lang_id, bodyp] or not forms_by_concept[lang_id, obj]:
                return 'None'
            elif forms_by_concept[lang_id, bodyp] & forms_by_concept[lang_id, obj]:
                return 'True'
            else:
                return 'False'

        form_index = collections.defaultdict(list)
        for lang_forms in forms_by_language.values():
            for form in lang_forms:
                lang_id = form['Language_ID']
                gloss = form['Concepticon_Gloss']
                phon = form['Form']
                form_index[lang_id, gloss, phon] = form['ID']
        values = [
            {
                'ID': '{}-{}'.format(lang['ID'], feat['ID']),
                'Language_ID': lang['ID'],
                'Parameter_ID': feat['ID'],
                'Value': _colex_value(lang['ID'], feat['Bodypart'], feat['Object']),
                'Code_ID': code_id(
                    feat['ID'],
                    _colex_value(lang['ID'], feat['Bodypart'], feat['Object'])),
                'Example_IDs': sorted(
                    form_index[lang['ID'], concept, form]
                    for concept in (feat['Bodypart'], feat['Object'])
                    for form in forms_by_concept[lang['ID'], concept]),
            }
            for lang in languages.values()
            for feat in features]

        languages_with_data = collections.Counter(
            val['Language_ID']
            for val in values
            if val.get('Value', 'None') != 'None')
        language_table = [
            lang
            for lang in languages.values()
            if languages_with_data.get(lang['ID'], 0) >= 20]
        values = [
            val
            for val in values
            if languages_with_data.get(val['Language_ID'], 0) >= 20]

        remaining_concepts = {
            concept
            for feature in features
            for concept in (feature['Bodypart'], feature['Object'])}
        forms_by_language = {
            lang_id: forms
            for lang_id, forms in forms_by_language.items()
            if languages_with_data.get(lang_id, 0) >= 20}
        example_table = [
            {
                'ID': form['ID'],
                'Language_ID': form['Language_ID'],
                'Primary_Text': form['Form'],
                'Translated_Text': form['Concepticon_Gloss'],
            }
            for lang_forms in forms_by_language.values()
            for form in lang_forms
            if form['Concepticon_Gloss'] in remaining_concepts]

        # Write CLDF data

        self._schema(args.writer)

        features.sort(key=lambda f: f['ID'])
        codes.sort(key=lambda c: c['ID'])
        language_table.sort(key=lambda l: l['ID'])
        values.sort(key=lambda v: v['ID'])
        example_table.sort(key=lambda e: e['ID'])

        args.writer.objects['ParameterTable'] = features
        args.writer.objects['CodeTable'] = codes
        args.writer.objects['LanguageTable'] = language_table
        args.writer.objects['ExampleTable'] = example_table
        args.writer.objects['ValueTable'] = values
        args.writer.objects['ContributionTable'] = contributions
        args.writer.objects['collections.csv'] = cldf_colls
