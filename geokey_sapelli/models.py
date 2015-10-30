import json
import csv
from django.db.models import (
    Model,
    OneToOneField,
    IntegerField,
    ImageField,
    ForeignKey,
    CharField,
    BooleanField
)

from geokey.contributions.models import Observation

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
    sapelli_fingerprint = IntegerField()

    objects = SapelliProjectManager()

    def get_description(self):
        """
        TODO
        """
        description = {}
        # GeoKey project id:
        description['geokey_project_id'] = self.project.id
        # Sapelli project id:
        description['sapelli_project_id'] = self.sapelli_id
        # Sapelli project fingerprint:
        description['sapelli_project_fingerprint'] = self.sapelli_fingerprint
        # Mapping of Sapelli Form ids to GeoKey category ids:
        description['form_category_mappings'] = []
        for form in self.forms.all():
            description['form_category_mappings'].append({'sapelli_form_id': form.sapelli_id, 'geokey_category_id': form.category.id})
        return description

    def import_from_csv(self, user, form_id, csvfile):
        """
        Reads an uploaded CSV file and creates the contributions and returns
        the number of contributions created, updated and ignored.
        
        Parameter
        ---------
        user : geokey.users.models.User
            User who uploaded the CSV. Will be used as the creater of each
            contribution.
        form_id : int
            Identifies the SapelliForm that is used to parse the incoming
            data. Has to be set by the uploading user in the upload form.
            Note that the id value of SapelliForm is the same as the id of
            the GeoKey category that corresponds to it. So the parameter
            could just as well be called 'category_id'.
        csvfile : django.core.files.File
            The file that was uploaded

        Returns
        -------
        int
            The number of contributions created
        int
            The number of contributions updated
        int
            The number of contributions ignored
        """
		# TODO read Sapelli Form id (String!) from the csv file header and get corresponding SapelliForm that way!
        form = self.forms.get(pk=form_id)
        location = form.location_fields.all()[0].sapelli_id
        reader = csv.DictReader(csvfile)
        imported_features = 0
        updated_features = 0
        ignored_features = 0

        for row in reader:
            feature = {
                "location": {
                    "geometry": '{ "type": "Point", "coordinates": '
                                '[%s, %s] }' % (
                                    float(row['%s.Longitude' % location]),
                                    float(row['%s.Latitude' % location])
                                )
                },
                "properties": {
                    "DeviceId": row['DeviceID'],
                    "StartTime": row['StartTime']
                },
                "meta": {
                    "category": form.category.id
                }
            }

            for sapelli_field in form.fields.all():
                key = sapelli_field.field.key
                sapelli_id = sapelli_field.sapelli_id.replace(' ', '_')

                value = row[sapelli_id]

                if sapelli_field.truefalse:
                    value = 0 if value == 'false' else 1

                if sapelli_field.items.count() > 0:
                    leaf = sapelli_field.items.get(number=value)
                    value = leaf.lookup_value.id

                feature['properties'][key] = value

            from geokey.contributions.serializers import (ContributionSerializer)

            try:
                observation = self.project.observations.get(
                    category_id=form.category.id,
                    properties__at_StartTime=row['StartTime'],
                    properties__at_DeviceId=row['DeviceID']
                )

                equal = True

                if json.loads(feature['location']['geometry']) != json.loads(observation.location.geometry.json):
                    equal = False

                if len(feature['properties']) != len(observation.properties):
                    equal = False

                for key in feature['properties']:
                    if feature['properties'][key] != observation.properties[key]:
                        equal = False

                if not equal:
                    serializer = ContributionSerializer(
                        observation,
                        data=feature,
                        context={'user': user, 'project': self.project}
                    )

                    if serializer.is_valid(raise_exception=True):
                        serializer.save()

                    updated_features += 1
                else:
                    ignored_features += 1
            except Observation.DoesNotExist:
                serializer = ContributionSerializer(
                    data=feature,
                    context={'user': user, 'project': self.project}
                )

                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                imported_features += 1

        return imported_features, updated_features, ignored_features


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
    truefalse = BooleanField(default=False)


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
