import xml.etree.ElementTree as ET
from os.path import dirname, normpath, abspath, join
from unittest import TestCase

from django.core.files import File
from django.conf import settings

from geokey.users.tests.model_factories import UserF
from geokey.categories.tests.model_factories import CategoryFactory
from geokey.categories.models import Category, NumericField, DateTimeField

from ..helper.xml_parsers import (
    extract_sapelli, parse_decision_tree, parse_list_items, parse_form,
    parse_text_element, parse_orientation_element, parse_checkbox_element,
    parse_button_element, parse_base_field, parse_list, parse_location_element
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
        self.assertEqual(len(form.get('locations')), 1)
        self.assertEqual(len(form.get('fields')), 10)

    def test_parse_form_without_id(self):
        element = ET.XML('<Form name="Lefini" startField="Situation" end="_LOOP" shortcut="true" endVibrate="true" shortcutImage="Elephant.png" storeEndTime="true" audioFeedback="NONE"></Form>')
        form = parse_form(element)
        self.assertEqual(form.get('sapelli_id'), 'Lefini')

    def test_parse_choice(self):
        element = ET.XML('<Choice id="Garden Feature" rows="2" cols="2">'
                         '<Choice value="Flowers" img="flowers.png" rows="3" '
                         'cols="2"><Choice value="Red Flowers" '
                         'img="red flowers.png"/><Choice value="Blue Flowers" '
                         'img="blue flowers.png"/><Choice value="Yellow '
                         'Flowers" img="yellow flowers.png"/></Choice><Choice '
                         'value="Animals" img="Sheep.png" rows="2" cols="1">'
                         '<Choice value="Two Legged Animal" '
                         'img="Chicken.png"/><Choice value="Four Legged '
                         'Animal" img="Sheep.png"/></Choice></Choice>')
        items = parse_list_items(element, 'Choice')
        self.assertEqual(len(items), 5)

    def test_parse_base_field(self):
        element = ET.XML('<Text caption="Text no-caps:" '
                         'description="Text no-caps:" content="text" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_base_field(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('description'), 'Text no-caps:')
        self.assertEqual(result.get('required'), False)

        element = ET.XML('<Text caption="Text no-caps:" '
                         'description="Text no-caps:" content="text" '
                         'autoCaps="none" optional="false" id="text"/>')
        result = parse_base_field(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('description'), 'Text no-caps:')
        self.assertEqual(result.get('required'), True)

        element = ET.XML('<Text caption="Text no-caps:" '
                         'description="Text no-caps:" content="text" '
                         'autoCaps="none" id="text"/>')
        result = parse_base_field(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('description'), 'Text no-caps:')
        self.assertEqual(result.get('required'), True)

    def test_parse_list(self):
        element = ET.XML('<List id="Community" captions="Province:;Community:"'
                         ' optional="false" editable="false" preSelectDefault='
                         '"false"><Item value="Community P1.1"/><Item value='
                         '"Community P1.2"/><Item value="Community P2.1"/>'
                         '<Item value="Community P2.2"/><Item value="Community'
                         ' P2.3"/></List>')
        field = parse_list(element)
        self.assertEqual(field.get('sapelli_id'), 'Community')
        self.assertEqual(field.get('geokey_type'), 'LookupField')
        self.assertEqual(len(field.get('items')), 5)

    def test_parse_multilist(self):
        element = ET.XML('<MultiList id="Community" captions="Province:;'
                         'Community:" optional="false" editable="false" '
                         'preSelectDefault="false"><Item value="Province 1">'
                         '<Item value="Community P1.1"/><Item value="'
                         'Community P1.2"/></Item><Item value="Province 2">'
                         '<Item value="Community P2.1"/><Item value="Community'
                         ' P2.2"/><Item value="Community P2.3"/></Item><Item '
                         'value="Province 3"/></MultiList>')
        items = parse_list_items(element, 'Item')
        self.assertEqual(len(items), 6)

    def test_parse_list_items(self):
        element = ET.XML('<List id="Community" captions="Province:;Community:"'
                         ' optional="false" editable="false" preSelectDefault='
                         '"false"><Item value="Community P1.1"/><Item value='
                         '"Community P1.2"/><Item value="Community P2.1"/>'
                         '<Item value="Community P2.2"/><Item value="Community'
                         ' P2.3"/></List>')
        items = parse_list_items(element, 'Item')
        self.assertEqual(len(items), 5)

    def test_parse_text_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="text" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), False)

    def test_parse_optional_text_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="text" '
                         'autoCaps="none" optional="false" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), True)

        element = ET.XML('<Text caption="Text no-caps:" content="text" '
                         'autoCaps="none" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), True)

    def test_parse_password_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="Password" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), False)

    def test_parse_email_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="Email" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), False)

    def test_parse_phone_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="PhoneNumber" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'TextField')
        self.assertEqual(result.get('required'), False)

    def test_parse_number_element(self):
        element = ET.XML('<Text caption="Text no-caps:" content="UnsignedInt" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'NumericField')
        self.assertEqual(result.get('required'), False)

        element = ET.XML('<Text caption="Text no-caps:" content="SignedInt" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'NumericField')
        self.assertEqual(result.get('required'), False)

        element = ET.XML('<Text caption="Text no-caps:" '
                         'content="UnsignedFloat" autoCaps="none" '
                         'optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'NumericField')
        self.assertEqual(result.get('required'), False)

        element = ET.XML('<Text caption="Text no-caps:" content="SignedFloat" '
                         'autoCaps="none" optional="true" id="text"/>')
        result = parse_text_element(element)
        self.assertEqual(result.get('sapelli_id'), 'text')
        self.assertEqual(result.get('caption'), 'Text no-caps:')
        self.assertEqual(result.get('geokey_type'), 'NumericField')
        self.assertEqual(result.get('required'), False)

    def test_parse_orientation_element(self):
        element = ET.XML('<Orientation id="orientationField" optional="false" '
                         'storeAzimuth="true" storePitch="true" '
                         'storeRoll="true" />')
        fields = parse_orientation_element(element)
        self.assertEqual(len(fields), 3)
        for field in fields:
            self.assertIn(field.get('caption'), ['Azimuth', 'Pitch', 'Roll'])
            self.assertEqual(field.get('geokey_type'), 'NumericField')

        element = ET.XML('<Orientation id="orientationField" '
                         'optional="false" />')
        fields = parse_orientation_element(element)
        self.assertEqual(len(fields), 3)
        for field in fields:
            self.assertIn(field.get('caption'), ['Azimuth', 'Pitch', 'Roll'])
            self.assertEqual(field.get('geokey_type'), 'NumericField')

        element = ET.XML('<Orientation id="orientationField" optional="false" '
                         'storeAzimuth="false" storePitch="true" '
                         'storeRoll="true" />')
        fields = parse_orientation_element(element)
        self.assertEqual(len(fields), 2)
        for field in fields:
            self.assertIn(field.get('caption'), ['Pitch', 'Roll'])
            self.assertEqual(field.get('geokey_type'), 'NumericField')

        element = ET.XML('<Orientation id="orientationField" optional="false" '
                         'storeAzimuth="false" storePitch="false" '
                         'storeRoll="true" />')
        fields = parse_orientation_element(element)
        self.assertEqual(len(fields), 1)
        for field in fields:
            self.assertIn(field.get('caption'), ['Roll'])
            self.assertEqual(field.get('geokey_type'), 'NumericField')

    def test_parse_checkbox_element(self):
        element = ET.XML('<Check id="eatsPork" caption="Do you eat pork?" '
                         'optional="false" defaultValue="false" />')

        result = parse_checkbox_element(element)
        self.assertEqual(result.get('sapelli_id'), 'eatsPork')
        self.assertEqual(result.get('caption'), 'Do you eat pork?')
        self.assertEqual(result.get('geokey_type'), 'LookupField')
        self.assertEqual(len(result.get('items')), 2)
        for item in result.get('items'):
            self.assertIn(item.get('value'), ['false', 'true'])

    def test_parse_button_element(self):
        element = ET.XML('<Button id="trainTimes" caption="Train" '
                         'column="datetime" optional="false" />')
        result = parse_button_element(element)
        self.assertEqual(result.get('sapelli_id'), 'trainTimes')
        self.assertEqual(result.get('caption'), 'Train')
        self.assertEqual(result.get('geokey_type'), 'DateTimeField')

        element = ET.XML('<Button id="trainTimes" caption="Train" '
                         'column="boolean" optional="false" />')
        result = parse_button_element(element)
        self.assertEqual(result.get('sapelli_id'), 'trainTimes')
        self.assertEqual(result.get('caption'), 'Train')
        self.assertEqual(result.get('geokey_type'), 'LookupField')
        self.assertEqual(len(result.get('items')), 2)
        for item in result.get('items'):
            self.assertIn(item.get('value'), ['false', 'true'])

        element = ET.XML('<Button id="trainTimes" caption="Train" '
                         'column="none" optional="false" />')
        result = parse_button_element(element)
        self.assertIsNone(result)

    def test_parse_location_field(self):
        element = ET.XML('<Location id="Location" maxAccuracyRadius="40.0" '
                         'useBestKnownLocationOnTimeout="false" '
                         'storeAltitude="false" jump="Confirmation" '
                         'skipOnBack="true" />')
        result = parse_location_element(element)
        self.assertEqual(result.get('sapelli_id'), 'Location')


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
                'locations': [{
                    'sapelli_id': 'Position'
                }],
                'fields': [{
                    'sapelli_id': 'Text',
                    'geokey_type': 'TextField',
                }, {
                    'sapelli_id': 'list',
                    'geokey_type': 'LookupField',
                    'items': [
                        {'value': 'value 1'},
                        {'value': 'value 2'},
                        {'value': 'value 3'},
                        {'value': 'value 4'},
                        {'value': 'value 5'}
                    ]
                }, {
                    'sapelli_id': 'Garden Feature',
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
        directory = normpath(join(dirname(abspath(__file__)), 'files'))

        geokey_project = create_project(project, UserF.create(), directory)
        self.assertEqual(geokey_project.name, 'Mapping Cultures')
        self.assertEqual(geokey_project.sapelli_project.sapelli_id, 1111)
        self.assertEqual(geokey_project.categories.count(), 1)

        category = geokey_project.categories.all()[0]
        self.assertEqual(category.name, 'Horniman Gardens')
        self.assertEqual(category.sapelli_form.location_fields.count(), 1)
        self.assertEqual(category.fields.count(), 5)

        field = category.fields.get(key='list')
        self.assertEqual(field.lookupvalues.count(), 5)

        field = category.fields.get(key='garden-feature')
        self.assertEqual(field.lookupvalues.count(), 14)
