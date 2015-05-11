from django.template.defaultfilters import slugify
from django.core.files import File

from geokey.projects.models import Project
from geokey.categories.models import Category, Field, LookupValue

from ..models import (
    SapelliProject, SapelliForm, SapelliChoiceRoot, SapelliChoice
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


def create_project(project, user, tmp_path):
    geokey_project = Project.create(
        project.get('name'),
        '',
        True,
        False,
        user
    )

    sapelli_project = SapelliProject.objects.create(
        project=geokey_project,
        sapelli_id=project.get('sapelli_id')
    )

    for form in project.get('forms'):
        category = Category.objects.create(
            project=geokey_project,
            creator=user,
            name=form.get('sapelli_id'),
            description='',
            default_status='active',
            create_grouping=True
        )
        sapelli_form = SapelliForm.objects.create(
            category=category,
            sapelli_project=sapelli_project,
            sapelli_id=form.get('sapelli_id')
        )

        create_implicit_fields(category)

        for choice_root in form.get('fields'):
            field = Field.create(
                choice_root.get('sapelli_id'),
                slugify(choice_root.get('sapelli_id')),
                '',
                False,
                category,
                'LookupField'
            )

            sapelli_choice_root = SapelliChoiceRoot.objects.create(
                sapelli_form=sapelli_form,
                sapelli_id=choice_root.get('sapelli_id'),
                select_field=field
            )

            for idx, choice in enumerate(choice_root.get('choices')):
                path = tmp_path + '/img/' + choice.get('img')
                img_file = File(open(path, 'rb'))
                value = LookupValue.objects.create(
                    name=choice.get('value'),
                    field=field
                )
                SapelliChoice.objects.create(
                    lookup_value=value,
                    sapelli_choice_root=sapelli_choice_root,
                    number=idx,
                    image=img_file
                )

    return geokey_project
