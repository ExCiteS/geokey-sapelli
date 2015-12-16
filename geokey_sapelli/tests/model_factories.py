import factory
from StringIO import StringIO
from PIL import Image

from os.path import dirname, normpath, abspath, join

from django.core.files.base import ContentFile

from geokey.projects.tests.model_factories import ProjectFactory
from geokey.categories.tests.model_factories import (
    CategoryFactory,
    FieldFactory,
    LookupFieldFactory,
    LookupValueFactory,
    TextFieldFactory
)

from ..models import (
    SapelliProject,
    SapelliForm,
    SapelliField,
    SapelliItem,
    LocationField
)


def get_image(file_name='test.png', width=200, height=200):
    image_file = StringIO()
    image = Image.new('RGBA', size=(width, height), color=(255, 0, 255))
    image.save(image_file, 'png')
    image_file.seek(0)

    the_file = ContentFile(image_file.read(), file_name)
    the_file.content_type = 'image/png'

    return the_file


class SapelliProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SapelliProject

    geokey_project = factory.SubFactory(ProjectFactory)
    sapelli_id = factory.Sequence(lambda n: n)
    sapelli_fingerprint = factory.Sequence(lambda n: n)


class SapelliFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SapelliForm

    category = factory.SubFactory(CategoryFactory)
    sapelli_project = factory.SubFactory(SapelliProjectFactory)
    sapelli_id = factory.Sequence(lambda n: 'Form %s' % n)


class SapelliLocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocationField

    sapelli_form = factory.SubFactory(SapelliFormFactory)
    sapelli_id = 'Location'


class SapelliFieldFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SapelliField

    sapelli_form = factory.SubFactory(SapelliFormFactory)
    field = factory.SubFactory(FieldFactory)
    sapelli_id = factory.Sequence(lambda n: 'ChoiceRoot %s' % n)


class SapelliChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SapelliItem

    lookup_value = factory.SubFactory(LookupValueFactory)
    image = get_image()
    number = factory.Sequence(lambda n: n)
    sapelli_field = factory.SubFactory(SapelliFieldFactory)


def create_horniman_sapelli_project(user):
    geokey_project = ProjectFactory.create(
        add_admins=[user],
        **{'name': 'Mapping Cultures (v1.1)'}
    )
    geokey_cat = CategoryFactory.create(**{
        'name': 'Horniman Gardens',
        'project': geokey_project
    })
    select_field = LookupFieldFactory.create(**{
        'name': 'Garden_Feature',
        'key': 'garden_feature',
        'category': geokey_cat
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Red Flowers'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Blue Flowers'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Yellow Flowers'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Edible Plants'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Medicinal Plants'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Two Legged Animal'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Four Legged Animal'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Old Bench With Memorial'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Old Bench with No Memorial'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'New Bench With Memorial'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'New Bench with No Memorial'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Covered Bin'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Uncovered Bin'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Dog Bin'
    })

    sapelli_project = SapelliProjectFactory.create(**{
        'geokey_project': geokey_project,
        'name': 'Mapping Cultures',
        'variant': None,
        'version': '1.1',
        'sapelli_id': 1111,
        'sapelli_fingerprint': -1001003931,
        'sapelli_model_id': 55263534870692951,
        'dir_path': None,
        'sap_path': normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
    })
    form = SapelliFormFactory.create(**{
        'category': geokey_cat,
        'sapelli_project': sapelli_project,
        'sapelli_id': 'Horniman Gardens',
        'sapelli_model_schema_number': 1
    })
    SapelliLocationFactory.create(**{
        'sapelli_form': form,
        'sapelli_id': 'Position'
    })
    choice_root = SapelliFieldFactory.create(**{
        'sapelli_form': form,
        'field': select_field,
        'sapelli_id': 'Garden_Feature'
    })

    for idx, value in enumerate(select_field.lookupvalues.all()):
        SapelliChoiceFactory.create(**{
            'lookup_value': value,
            'number': idx,
            'sapelli_field': choice_root
        })

    return sapelli_project


def create_textunicode_sapelli_project(user):
    geokey_project = ProjectFactory.create(
        add_admins=[user],
        **{'name': u'TextUnicode_\u6d4b\u8bd5_(v0.23)'}
    )
    geokey_cat = CategoryFactory.create(**{
        'name': 'TextTest',
        'project': geokey_project
    })
    text_field = TextFieldFactory.create(**{
        'name': 'txtText',
        'key': 'txttext',
        'category': geokey_cat
    })
    sapelli_project = SapelliProjectFactory.create(**{
        'geokey_project': geokey_project,
        'name': 'TextUnicode',
        'variant': '\u6d4b\u8bd5',
        'version': '0.23',
        'sapelli_id': 1337,
        'sapelli_fingerprint': 1961882530,
        'sapelli_model_id': 32914926972437817,
        'dir_path': None,
        'sap_path': normpath(join(dirname(abspath(__file__)), 'files/TextUnicode.sap'))
    })
    form = SapelliFormFactory.create(**{
        'category': geokey_cat,
        'sapelli_project': sapelli_project,
        'sapelli_id': 'TextTest',
        'sapelli_model_schema_number': 1
    })
    SapelliLocationFactory.create(**{
        'sapelli_form': form,
        'sapelli_id':  u'\u4f4d\u7f6e'
    })
    sap_text_field = SapelliFieldFactory.create(**{
        'sapelli_form': form,
        'field': text_field,
        'sapelli_id': 'txtText'
    })

    return sapelli_project
