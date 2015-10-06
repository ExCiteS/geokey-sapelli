from django.template.defaultfilters import slugify
from django.core.files import File

from geokey.projects.models import Project
from geokey.categories.models import Category, Field, LookupValue

from ..models import (
    SapelliProject, SapelliForm, SapelliField, SapelliItem, LocationField
)


implicit_fields = [{
    'name': 'Device Id',
    'key': 'DeviceId',
    'type': 'NumericField'
}, {
    'name': 'Start Time',
    'key': 'StartTime',
    'type': 'DateTimeField'
}]


def create_implicit_fields(category):
    for field in implicit_fields:
        Field.create(
            field.get('name'),
            field.get('key'),
            '',
            False,
            category,
            field.get('type')
        )


def create_project(sapelli_project_info, user, tmp_path):
    geokey_project = Project.create(
        sapelli_project_info.get('name'),
        '',
        True,
        False,
        user
    )

    sapelli_project = SapelliProject.objects.create(
        project=geokey_project,
        sapelli_id=sapelli_project_info.get('sapelli_id'),
        sapelli_fingerprint=sapelli_project_info.get('sapelli_fingerprint')
    )

    for form in sapelli_project_info.get('forms'):
        category = Category.objects.create(
            project=geokey_project,
            creator=user,
            name=form.get('sapelli_id'),
            description='',
            default_status='active'
        )
        sapelli_form = SapelliForm.objects.create(
            category=category,
            sapelli_project=sapelli_project,
            sapelli_id=form.get('sapelli_id')
        )

        create_implicit_fields(category)

        for location in form.get('locations'):
            LocationField.objects.create(
                sapelli_form=sapelli_form,
                sapelli_id=location.get('sapelli_id'),
            )

        for field in form.get('fields'):
            field_type = field.get('geokey_type')

            name = field.get('caption')
            if not name:
                name = field.get('sapelli_id')

            geokey_field = Field.create(
                name,
                slugify(name),
                field.get('description'),
                False,
                category,
                field_type
            )

            sapelli_field = SapelliField.objects.create(
                sapelli_form=sapelli_form,
                sapelli_id=field.get('sapelli_id'),
                field=geokey_field,
                truefalse=field.get('truefalse')
            )

            if field_type == 'LookupField':
                for idx, item in enumerate(field.get('items')):
                    img = item.get('img')
                    img_file = None
                    if img:
                        path = tmp_path + '/img/' + item.get('img')
                        img_file = File(open(path, 'rb'))
                        # try:
                        #     img_file = File(open(path, 'rb'))
                        # except IOError:
                        #     pass

                    value = LookupValue.objects.create(
                        name=item.get('value'),
                        field=geokey_field
                    )
                    SapelliItem.objects.create(
                        lookup_value=value,
                        sapelli_choice_root=sapelli_field,
                        number=idx,
                        image=img_file
                    )

    return geokey_project
