import factory

from datetime import datetime, timedelta
from pytz import utc

from os.path import dirname, normpath, abspath, join

from django.conf import settings
from django.utils import timezone

from geokey.applications.tests.model_factories import ApplicationFactory
from geokey.projects.tests.model_factories import ProjectFactory
from geokey.categories.tests.model_factories import (
    CategoryFactory,
    FieldFactory,
    LookupFieldFactory,
    LookupValueFactory,
    TextFieldFactory
)
from geokey.users.tests.model_factories import UserFactory, AccessTokenFactory

from ..models import (
    SapelliProject,
    SapelliForm,
    SapelliField,
    SapelliItem,
    SapelliLogFile,
    LocationField,
    SAPDownloadQRLink,
)


class GeoKeySapelliApplicationFactory(ApplicationFactory):
    client_id = settings.SAPELLI_CLIENT_ID
    authorization_grant_type = 'password'


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
        'name': 'Red Flowers',
        'symbol': 'red flowers.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Blue Flowers',
        'symbol': 'blue flowers.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Yellow Flowers',
        'symbol': 'yellow flowers.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Edible Plants',
        'symbol': 'BeenTold.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Medicinal Plants',
        'symbol': 'Medicine.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Two Legged Animal',
        'symbol': 'Chicken.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Four Legged Animal',
        'symbol': 'Sheep.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Old Bench With Memorial',
        'symbol': 'memorial.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Old Bench with No Memorial',
        'symbol': 'no memorial'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'New Bench With Memorial',
        'symbol': 'memorial.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'New Bench with No Memorial',
        'symbol': 'no memorial.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Covered Bin',
        'symbol': 'covered bin.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Uncovered Bin',
        'symbol': 'uncovered bin.png'
    })
    LookupValueFactory.create(**{
        'field': select_field,
        'name': 'Dog Bin',
        'symbol': 'dog bin.png'
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
        'sapelli_id': u'\u4f4d\u7f6e'
    })
    sap_text_field = SapelliFieldFactory.create(**{
        'sapelli_form': form,
        'field': text_field,
        'sapelli_id': 'txtText'
    })

    return sapelli_project


class SapelliLogFileFactory(factory.django.DjangoModelFactory):
    """An instance factory for SapelliLogFile model."""

    name = 'Collector_2015-01-20T18.02.12.log'
    creator = factory.SubFactory(UserFactory)
    created_at = datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc)
    sapelli_project = factory.SubFactory(SapelliProjectFactory)
    file = normpath(join(
        dirname(abspath(__file__)),
        'files/Collector_2015-01-20T18.02.12.log'))

    class Meta:
        """Class meta information."""

        model = SapelliLogFile


class SAPDownloadQRLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SAPDownloadQRLink

    access_token = factory.SubFactory(AccessTokenFactory)
    sapelli_project = factory.SubFactory(SapelliProjectFactory)


def create_qr_link(app, user, project):
    access_token = AccessTokenFactory.create(**{
        'user': user,
        'application': app,
        'expires': timezone.now() + timedelta(days=1),
        'token': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
        'scope': 'read'
    })

    qr_link = SAPDownloadQRLinkFactory.create(**{
        'access_token': access_token,
        'sapelli_project': project
    })

    return qr_link
