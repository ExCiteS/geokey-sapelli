import factory
from StringIO import StringIO
from PIL import Image

from django.core.files.base import ContentFile

from geokey.projects.tests.model_factories import ProjectF
from geokey.categories.tests.model_factories import (
    CategoryFactory,
    FieldFactory,
    LookupFieldFactory,
    LookupValueFactory
)

from ..models import (
    SapelliProject,
    SapelliForm,
    SapelliField,
    SapelliItem
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

    project = factory.SubFactory(ProjectF)
    sapelli_id = factory.Sequence(lambda n: n)


class SapelliFormFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SapelliForm

    category = factory.SubFactory(CategoryFactory)
    sapelli_project = factory.SubFactory(SapelliProjectFactory)
    sapelli_id = factory.Sequence(lambda n: 'Form %s' % n)


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
    sapelli_choice_root = factory.SubFactory(SapelliFieldFactory)


def create_full_project(user):
    geokey_project = ProjectF.create(
        add_admins=[user],
        **{'name': 'Mapping Cultures'}
    )
    geokey_cat = CategoryFactory.create(**{
        'name': 'Horniman Gardens',
        'project': geokey_project
    })
    select_field = LookupFieldFactory.create(**{
        'name': 'Garden Feature',
        'key': 'garden-feature',
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

    project = SapelliProjectFactory.create(**{'project': geokey_project})
    form = SapelliFormFactory.create(**{
        'category': geokey_cat,
        'sapelli_project': project,
        'sapelli_id': 'Horniman Gardens'
    })
    choice_root = SapelliFieldFactory.create(**{
        'sapelli_form': form,
        'field': select_field,
        'sapelli_id': 'Garden Feature'
    })

    for idx, value in enumerate(select_field.lookupvalues.all()):
        SapelliChoiceFactory.create(**{
            'lookup_value': value,
            'number': idx,
            'sapelli_choice_root': choice_root
        })

    return project
