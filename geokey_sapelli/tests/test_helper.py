import xml.etree.ElementTree as ET
from os.path import dirname, normpath, abspath, join
from unittest import TestCase

from django.core.files import File
from django.conf import settings

from geokey.users.tests.model_factories import UserF
from geokey.categories.tests.model_factories import CategoryFactory
from geokey.categories.models import Category, NumericField, DateTimeField

from ..helper.xml_parsers import (
    extract_sapelli, parse_decision_tree, parse_choice, parse_form
)
from ..helper.project_mapper import create_project, create_implicit_fields


class TestParsers(TestCase):
    def test_extract_file(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        directory = extract_sapelli(file)
        self.assertEqual(directory, settings.MEDIA_ROOT + '/tmp/Horniman.sap')

    def test_parse_decision_tree(self):
        file = normpath(join(dirname(abspath(__file__)), 'files/PROJECT.xml'))
        project = parse_decision_tree(file)

        self.assertEqual(project.get('name'), 'Mapping Cultures')
        self.assertEqual(project.get('sapelli_id'), 1111)
        self.assertEqual(len(project.get('forms')), 1)

    def test_parse_form(self):
        file = normpath(join(dirname(abspath(__file__)), 'files/PROJECT.xml'))
        choice = ET.parse(file).getroot().find('Form')
        form = parse_form(choice)
        self.assertEqual(form.get('sapelli_id'), 'Horniman Gardens')
        self.assertEqual(len(form.get('fields')), 2)

    def test_parse_choice(self):
        file = normpath(join(dirname(abspath(__file__)), 'files/PROJECT.xml'))
        choice = ET.parse(file).getroot().find('Form').find('Choice')
        choice = parse_choice(choice)
        self.assertEqual(len(choice), 14)


class TestCreateProject(TestCase):
    def test_create_implicit_fields(self):
        category = CategoryFactory.create()
        create_implicit_fields(category)

        ref_cat = Category.objects.get(pk=category.id)
        self.assertEqual(ref_cat.fields.count(), 2)
        for field in ref_cat.fields.select_subclasses():
            self.assertIn(field.name, ['Device Id', 'Start Time'])

            if field.name == 'Device Id':
                self.assertTrue(isinstance(field, NumericField))
            elif field.name == 'Start Time':
                self.assertTrue(isinstance(field, DateTimeField))

    def test_create_project(self):
        project = {
            'name': 'Mapping Cultures',
            'sapelli_id': 1111,
            'forms': [{
                'sapelli_id': 'Horniman Gardens',
                'fields': [{
                    'sapelli_id': 'Garden Feature',
                    'geokey_type': 'LookupField',
                    'choices': [{
                        'value': 'Red Flowers',
                        'img': 'red flowers.png'
                    }, {
                        'value': 'Blue Flowers',
                        'img': 'blue flowers.png'
                    }, {
                        'value': 'Yellow Flowers',
                        'img': 'yellow flowers.png'
                    }, {
                        'value': 'Edible Plants',
                        'img': 'BeenTold.png'
                    }, {
                        'value': 'Medicinal Plants',
                        'img': 'Medicine.png'
                    }, {
                        'value': 'Two Legged Animal',
                        'img': 'Chicken.png'
                    }, {
                        'value': 'Four Legged Animal',
                        'img': 'Sheep.png'
                    }, {
                        'value': 'Old Bench With Memorial',
                        'img': 'memorial.png'
                    }, {
                        'value': 'Old Bench with No Memorial',
                        'img': 'no memorial.png'
                    }, {
                        'value': 'New Bench With Memorial',
                        'img': 'memorial.png'
                    }, {
                        'value': 'New Bench with No Memorial',
                        'img': 'no memorial.png'
                    }, {
                        'value': 'Covered Bin',
                        'img': 'covered bin.png'
                    }, {
                        'value': 'Uncovered Bin',
                        'img': 'uncovered bin.png'
                    }, {
                        'value': 'Dog Bin',
                        'img': 'dog bin.png'
                    }]
                }]
            }]
        }
        directory = normpath(join(dirname(abspath(__file__)), 'files'))

        geokey_project = create_project(project, UserF.create(), directory)
        self.assertEqual(geokey_project.name, 'Mapping Cultures')
        self.assertEqual(geokey_project.sapelli_project.sapelli_id, 1111)
        self.assertEqual(geokey_project.categories.count(), 1)

        category = geokey_project.categories.all()[0]
        self.assertEqual(category.name, 'Horniman Gardens')
        self.assertEqual(category.fields.count(), 3)

        field = category.fields.get(key='garden-feature')
        self.assertEqual(field.lookupvalues.count(), 14)
