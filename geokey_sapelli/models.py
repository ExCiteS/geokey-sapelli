import csv
from django.db.models import (
    Model,
    OneToOneField,
    IntegerField,
    ImageField,
    ForeignKey,
    CharField
)

from .manager import SapelliProjectManager


class SapelliProject(Model):
    """
    Represents a Sapelli project. Is usually created by parsing a Sapelli
    decision tree.
    """
    project = OneToOneField(
        'projects.Project',
        primary_key=True,
        related_name='sapelli_project'
    )
    sapelli_id = IntegerField()

    objects = SapelliProjectManager()

    def import_from_csv(self, user, form_id, csvfile):
        """
        Reads an uploaded CSV file and creates the contributions and returns
        the number of contributions created.

        user : geokey.users.models.User
            User who uploaded the CSV. Will be used as the creater of each
            contribution.
        form_id : int
            Identifies the SapelliForm that is used to parse the incoming
            data. Has to be set by the uploading user in the upload form.
        csvfile : django.core.files.File
            The file that was uploaded

        Returns
        -------
        int
            The number of contributions created
        """
        form = self.forms.get(pk=form_id)
        reader = csv.DictReader(csvfile)
        imported_features = 0

        for row in reader:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(row['Position.Latitude']),
                        float(row['Position.Latitude'])
                    ]
                },
                "properties": {},
                "meta": {
                    "category": form.category.id
                }
            }

            for choice in form.choices.all():
                key = choice.select_field.key
                sapelli_id = choice.sapelli_id.replace(' ', '_')

                value = row[sapelli_id]
                leaf = choice.choices_leafs.get(number=value)

                feature['properties'][key] = leaf.lookup_value.id

            from geokey.contributions.serializers import ContributionSerializer
            serializer = ContributionSerializer(
                data=feature,
                context={'user': user, 'project': self.project}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()

            imported_features += 1

        return imported_features


class SapelliForm(Model):
    """
    Represents a Sapelli form. Is usually created by parsing a Sapelli
    decision tree.
    """
    category = OneToOneField(
        'categories.Category',
        primary_key=True,
        related_name='sapelli_form'
    )
    sapelli_project = ForeignKey(
        'SapelliProject',
        related_name='forms'
    )
    sapelli_id = CharField(max_length=255)


class SapelliChoiceRoot(Model):
    """
    Represents a Sapelli Choice element that has no Choice elements as parents.
    Is usually created by parsing a Sapelli decision tree.
    """
    sapelli_form = ForeignKey(
        'SapelliForm',
        related_name='choices'
    )
    select_field = ForeignKey(
        'categories.LookupField',
        related_name='sapelli_choice_root'
    )
    sapelli_id = CharField(max_length=255)


class SapelliChoice(Model):
    """
    Represents a Sapelli Choice element that has no Choice elements as childs.
    Is usually created by parsing a Sapelli decision tree.
    """
    lookup_value = OneToOneField(
        'categories.LookupValue',
        primary_key=True,
        related_name='sapelli_choice'
    )
    image = ImageField(upload_to='sapelli/choice')
    number = IntegerField()
    sapelli_choice_root = ForeignKey(
        'SapelliChoiceRoot',
        related_name='choices_leafs'
    )
