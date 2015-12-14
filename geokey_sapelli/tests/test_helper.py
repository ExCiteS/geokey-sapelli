import time
import copy
import xml.etree.ElementTree as ET
from os.path import dirname, normpath, abspath, join
from unittest import TestCase

from django.core.files import File
from django.conf import settings

from geokey.users.tests.model_factories import UserFactory
from geokey.categories.tests.model_factories import CategoryFactory
from geokey.categories.models import Category, NumericField, DateTimeField

from ..helper.sapelli_loader import load_from_sap, check_sap_file, get_sapelli_project_info
from ..models import SapelliProject
from ..helper.project_mapper import create_project, create_implicit_fields
from ..helper.sapelli_exceptions import SapelliException, SapelliSAPException, SapelliXMLException, SapelliDuplicateException

"""
Output of get_sapelli_project_info() for Horniman.sap,
except for the 'installation_path' key, which we left out here.
"""
horniman_sapelli_project_info = {
    'name': 'Mapping Cultures',
    'variant': None,
    'version': '1.1',
    'sapelli_id': 1111,
    'display_name': 'Mapping Cultures (v1.1)',
    'sapelli_fingerprint': -1001003931,
    'sapelli_model_id': 55263534870692951,
    'forms': [{
        'sapelli_id': 'Horniman Gardens',
        'sapelli_model_schema_number': 1,
        'stores_end_time': False,
        'locations': [{
            'sapelli_id': 'Position',
            'required': False,
            'truefalse': False,
            'caption': None,
            'description': None,
            'geokey_type': None
        }],
        'fields': [{
            'sapelli_id': 'Garden_Feature',
            'description': None,
            'caption': None,
            'truefalse': False,
            'required': True,
            'geokey_type': 'LookupField',
            'items': [
                {
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
                }
            ]
        }]
    }]
}


def with_stacktrace(func, *args):
    try:
        return func(*args)
    except SapelliSAPException, e:
        if e.java_stacktrace is not None:
            # make java stacktrace visible in test log:
            raise SapelliSAPException(str(e) + '\n' + e.java_stacktrace)
        else:
            raise e

class TestSapelliLoader(TestCase):
    def tearDown(self):
        # delete project(s):
        for sapelli_project in SapelliProject.objects.filter(sapelli_id__in=[horniman_sapelli_project_info['sapelli_id'], 1337]):
            try:
                sapelli_project.geokey_project.delete() # will also delete sapelli_project
            except BaseException, e:
                pass

    def test_check_sap_file_non_existing(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/' + str(time.time())))
        self.assertRaises(SapelliSAPException, check_sap_file, path)

    def test_check_sap_file_non_zip(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/img/ok.svg'))
        self.assertRaises(SapelliSAPException, check_sap_file, path)
        
    def test_check_sap_file_no_xml(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Empty.zip'))
        self.assertRaises(SapelliSAPException, check_sap_file, path)

    def test_check_sap_file_horniman(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        check_sap_file(path)
        
    def test_get_sapelli_project_info_horniman(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        sapelli_project_info = with_stacktrace(get_sapelli_project_info, path)
        sapelli_project_info.pop('installation_path', None)
        self.assertEquals(sapelli_project_info, horniman_sapelli_project_info)
        
    def test_load_from_sap_horniman(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        sapelli_project = with_stacktrace(load_from_sap, file, UserFactory.create())
        self.assertEqual(sapelli_project.name, horniman_sapelli_project_info['name'])
        self.assertEqual(sapelli_project.version, horniman_sapelli_project_info['version'])
        self.assertEqual(sapelli_project.geokey_project.name, horniman_sapelli_project_info['display_name'])
        self.assertEqual(sapelli_project.sapelli_id, horniman_sapelli_project_info['sapelli_id'])
        self.assertEqual(sapelli_project.sapelli_fingerprint, horniman_sapelli_project_info['sapelli_fingerprint'])
        self.assertEqual(sapelli_project.sapelli_model_id, horniman_sapelli_project_info['sapelli_model_id'])
        
    def test_load_from_sap_complex(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Complex.sap'))
        file = File(open(path, 'rb'))
        sapelli_project = with_stacktrace(load_from_sap, file, UserFactory.create())
        self.assertEqual(sapelli_project.name, horniman_sapelli_project_info['name'])
        self.assertEqual(sapelli_project.variant, '[Test]')
        self.assertEqual(sapelli_project.version, '2.0')
        self.assertEqual(sapelli_project.sapelli_id, horniman_sapelli_project_info['sapelli_id'])
        self.assertEqual(sapelli_project.sapelli_fingerprint, -421056405)
        self.assertEqual(sapelli_project.forms.count(), 2)
        
    def test_load_from_sap_unicode(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/TextUnicode.sap'))
        file = File(open(path, 'rb'))
        sapelli_project = with_stacktrace(load_from_sap, file, UserFactory.create())
        self.assertEqual(sapelli_project.name, 'TextUnicode')
        self.assertEqual(sapelli_project.variant, u'\u6d4b\u8bd5')
        self.assertEqual(sapelli_project.version, '0.23')
        self.assertEqual(sapelli_project.sapelli_id, 1337)
        self.assertEqual(sapelli_project.sapelli_fingerprint, 1961882530)
        self.assertEqual(sapelli_project.sapelli_model_id, 32914926972437817)

    def test_load_from_sap_no_location(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/NoLocation.sap'))
        file = File(open(path, 'rb'))
        self.assertRaises(SapelliSAPException, load_from_sap, file, UserFactory.create())


class TestProjectMapper(TestCase):
    def test_create_implicit_fields(self):
        category = CategoryFactory.create()
        create_implicit_fields(category, stores_end_time=True)
        ref_cat = Category.objects.get(pk=category.id)
        self.assertEqual(ref_cat.fields.count(), 3)
        for field in ref_cat.fields.select_subclasses():
            self.assertIn(field.name, ['Device Id', 'Start Time', 'End Time'])
            if field.key == 'DeviceId':
                self.assertTrue(isinstance(field, NumericField))
            elif field.key == 'StartTime':
                self.assertTrue(isinstance(field, DateTimeField))
            elif field.key == 'EndTime':
                self.assertTrue(isinstance(field, DateTimeField))

    def test_create_project(self):
        geokey_project = create_project(horniman_sapelli_project_info, UserFactory.create())
        self.assertEqual(geokey_project.name, horniman_sapelli_project_info['display_name'])
        self.assertEqual(geokey_project.sapelli_project.name, horniman_sapelli_project_info['name'])
        self.assertEqual(geokey_project.sapelli_project.version, horniman_sapelli_project_info['version'])
        self.assertEqual(geokey_project.sapelli_project.sapelli_id, horniman_sapelli_project_info['sapelli_id'])
        self.assertEqual(geokey_project.sapelli_project.sapelli_fingerprint, horniman_sapelli_project_info['sapelli_fingerprint'])
        self.assertEqual(geokey_project.sapelli_project.sapelli_model_id, horniman_sapelli_project_info['sapelli_model_id'])
        self.assertEqual(geokey_project.categories.count(), len(horniman_sapelli_project_info['forms']))

        category = geokey_project.categories.all()[0]
        self.assertEqual(category.name, horniman_sapelli_project_info['forms'][0]['sapelli_id'])
        self.assertEqual(category.sapelli_form.location_fields.count(), len(horniman_sapelli_project_info['forms'][0]['locations']))
        self.assertEqual(category.fields.count(),
            len(horniman_sapelli_project_info['forms'][0]['fields']) +
            (3 if horniman_sapelli_project_info['forms'][0]['stores_end_time'] else 2))

        field = category.fields.get(key='garden_feature')
        self.assertEqual(field.lookupvalues.count(), 14)
