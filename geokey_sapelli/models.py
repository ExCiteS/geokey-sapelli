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
        location = form.location_fields.all()[0].sapelli_id
        reader = csv.DictReader(csvfile)
        imported_features = 0

        for row in reader:
            try:
                feature = {
                    "location": {
                        "geometry": '{ "type": "Point", "coordinates": '
                                    '[%s, %s] }' % (
                                        float(row['%s.Longitude' % location]),
                                        float(row['%s.Latitude' % location])
                                    )
                    },
                    "properties": {},
                    "meta": {
                        "category": form.category.id
                    }
                }

                for sapelli_field in form.fields.all():
                    key = sapelli_field.field.key
                    sapelli_id = sapelli_field.sapelli_id.replace(' ', '_')

                    value = row[sapelli_id]

                    if sapelli_field.items:
                        leaf = sapelli_field.items.get(number=value)
                        value = leaf.lookup_value.id

                    feature['properties'][key] = value

                from geokey.contributions.serializers import (
                    ContributionSerializer)
                serializer = ContributionSerializer(
                    data=feature,
                    context={'user': user, 'project': self.project}
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                imported_features += 1
            except ValueError:
                pass

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


class LocationField(Model):
    """
    Represents a Location field.
    """
    sapelli_form = ForeignKey(
        'SapelliForm',
        related_name='location_fields'
    )
    sapelli_id = CharField(max_length=255)


class SapelliField(Model):
    """
    Represents a Sapelli input option, can be a Text input, a list or a choice
    root element.
    """
    sapelli_form = ForeignKey(
        'SapelliForm',
        related_name='fields'
    )
    field = ForeignKey(
        'categories.Field',
        related_name='sapelli_field'
    )
    sapelli_id = CharField(max_length=255)


class SapelliItem(Model):
    """
    Represents a Sapelli Choice element that has no Choice elements as childs.
    Is usually created by parsing a Sapelli decision tree.
    """
    lookup_value = OneToOneField(
        'categories.LookupValue',
        primary_key=True,
        related_name='sapelli_item'
    )
    image = ImageField(upload_to='sapelli/item', null=True)
    number = IntegerField()
    sapelli_choice_root = ForeignKey(
        'SapelliField',
        related_name='items'
    )
