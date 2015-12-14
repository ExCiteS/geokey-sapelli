import os

from django.template.defaultfilters import slugify
from django.core.files import File

from geokey.projects.models import Project
from geokey.categories.models import Category, Field, LookupValue

from ..models import (
    SapelliProject, SapelliForm, SapelliField, SapelliItem, LocationField
)
from .sapelli_exceptions import SapelliSAPException

implicit_fields = [{
    'name': 'Device Id',
    'key': 'DeviceId',
    'type': 'NumericField'
}, {
    'name': 'Start Time',
    'key': 'StartTime',
    'type': 'DateTimeField'
}, {
    'name': 'End Time',
    'key': 'EndTime',
    'type': 'DateTimeField'
}]


def create_implicit_fields(category, stores_end_time=False):
    for field in implicit_fields:
        if stores_end_time or field.get('key') != 'EndTime':
            Field.create(
                field.get('name'),
                field.get('key'),
                '',
                False,
                category,
                field.get('type')
            )


def create_project(sapelli_project_info, user):
    geokey_project = Project.create(
        sapelli_project_info.get('display_name'),
        ('Sapelli project id: %s;\nSapelli project fingerprint: %s;' % (
            sapelli_project_info.get('sapelli_id'),
            sapelli_project_info.get('sapelli_fingerprint'))),
        True,
        False,
        user
    )

    # If anyting below fails the geokey_project will be deleted:
    try:
        sapelli_project = SapelliProject.objects.create(
            geokey_project=geokey_project,
            name=sapelli_project_info.get('name'),
            variant=sapelli_project_info.get('variant'),
            version=sapelli_project_info.get('version'),
            sapelli_id=sapelli_project_info.get('sapelli_id'),
            sapelli_fingerprint=sapelli_project_info.get('sapelli_fingerprint'),
            sapelli_model_id=sapelli_project_info.get('sapelli_model_id'),
            path=sapelli_project_info.get('installation_path')
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
                sapelli_id=form.get('sapelli_id'),
                sapelli_model_schema_number=form.get('sapelli_model_schema_number')
            )
            
            create_implicit_fields(category, stores_end_time=form.get('stores_end_time'))

            if not form.get('locations'):
                try:
                    geokey_project.delete()
                except BaseException:
                    pass
                raise SapelliSAPException('geokey-sapelli only supports Sapelli Forms which have a Location field.')
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
                    # Loop over items:
                    for idx, item in enumerate(field.get('items')):
                        # Value:
                        value = LookupValue.objects.create(
                            name=item.get('value'),
                            field=geokey_field
                        )
                        # Image:
                        img_relative_path = item.get('img')
                        img_file = None
                        if img_relative_path and sapelli_project.path:
                            try:
                                img_file = File(open(os.path.join(sapelli_project.path, 'img/', img_relative_path), 'rb'))
                            except IOError:
                                pass
                        if img_file is not None:
                            img_path = img_file.name
                            img_file.close()
                        else:
                            img_path = None
                        # Create SapelliItem:
                        SapelliItem.objects.create(
                            lookup_value=value,
                            sapelli_field=sapelli_field,
                            number=idx,
                            image=img_path #pass the path, not the file (otherwise it may be duplicated)
                        )
    except BaseException, e:
        try: # delete geokey_project:
            geokey_project.delete()
        except BaseException:
            pass
        raise e

    return geokey_project
