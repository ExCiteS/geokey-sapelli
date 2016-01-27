import json
import re
import os
import shutil
from datetime import timedelta

from django.db import models
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from geokey.projects.models import Project
from geokey.contributions.models import Observation
from geokey.applications.models import Application

from oauth2_provider.models import AccessToken
from oauthlib.common import generate_token

from .manager import SapelliProjectManager

from .helper.sapelli_exceptions import SapelliException, SapelliCSVException

from .helper.csv_helpers import UnicodeDictReader


class SapelliProject(models.Model):
    """
    Represents a Sapelli project.
    """
    geokey_project = models.OneToOneField(
        'projects.Project',
        primary_key=True,
        related_name='sapelli_project'
    )
    name = models.CharField(max_length=255, default='')
    variant = models.CharField(max_length=63, null=True)
    version = models.CharField(max_length=63, default='0')
    sapelli_id = models.IntegerField()
    sapelli_fingerprint = models.IntegerField()
    sapelli_model_id = models.BigIntegerField(default=-1)
    dir_path = models.CharField(max_length=511, null=True)
    sap_path = models.CharField(max_length=511, null=True)

    objects = SapelliProjectManager()

    def delete(self):
        # Remove SAP file:
        try:
            os.remove(self.sap_path)
        except BaseException:
            pass
        # Remove project folder:
        try:
            shutil.rmtree(os.path.dirname(self.dir_path), ignore_errors=True)
        except BaseException:
            pass
        # Call super delete method:
        super(SapelliProject, self).delete()

    def get_description(self):
        """
        Generates a dictionary with all identifying information about the Sapelli/GeoKey project.

        Returns
        -------
        dict
            Dictionary describing the project
        """
        description = {}
        # GeoKey project id:
        description['geokey_project_id'] = self.geokey_project.id
        # GeoKey project name:
        description['geokey_project_name'] = self.geokey_project.name
        # Sapelli project name:
        description['sapelli_project_name'] = self.name
        # Sapelli project variant:
        description['sapelli_project_variant'] = self.variant
        # Sapelli project version:
        description['sapelli_project_version'] = self.version
        # Sapelli project id:
        description['sapelli_project_id'] = self.sapelli_id
        # Sapelli project fingerprint:
        description['sapelli_project_fingerprint'] = self.sapelli_fingerprint
        # Sapelli model id:
        description['sapelli_model_id'] = self.sapelli_model_id
        # Sapelli forms & corresponding GeoKey categories:
        description['sapelli_project_forms'] = []
        for form in self.forms.all():
            description['sapelli_project_forms'].append({
                'sapelli_form_id': form.sapelli_id,
                'sapelli_model_schema_number': form.sapelli_model_schema_number,
                'geokey_category_id': form.category.id})
        return description

    def import_from_csv(self, user, csv_file, form_category_id=None):
        """
        Reads an uploaded CSV file and creates the contributions and returns
        the number of contributions created, updated and ignored.

        Parameter
        ---------
        user : geokey.users.models.User
            User who uploaded the CSV. Will be used as the creator of each
            contribution.
        csv_file : django.core.files.File
            The file that was uploaded.
        form_category_id : int
            optionally identifies the GeoKey category backing the SapelliForm
            which generated the data in the CSV file. This is only really used
            if the CSV file header does not contain Form identification info
            (i.e. modelID & modelSchemaNumber).

        Returns
        -------
        int
            The number of contributions created
        int
            The number of contributions updated
        int
            The number of contributions ignored due to being duplicates
        int
            The number of contributions ignored due to lacking location coordinates

        Raises
        ------
        SapelliCSVException
            When no Sapelli Project/Form (known on this server, and accessible by this user) can be found
            which matches the one used to generate the data in the CSV file.
        """
        # Make sure form_category_id is an int (or None):
        if form_category_id is None or form_category_id == '':
            form_category_id = None
        else:
            form_category_id = int(form_category_id)

        # Check if we got a file at all:
        if csv_file is None:
            raise SapelliCSVException('No file provided')

        # Sapelli Collector produces CSV files in 'utf-8-sig' encoding (= UTF8 with BOM):
        reader = UnicodeDictReader(csv_file, encoding='utf-8-sig')

        # Parse modelID & modelSchemaNumber from header row:
        model_id = None
        model_schema_number = None
        try:
            model_id = int(re.match(
                r"modelID=(?P<model_id_str>[0-9]+)",
                [fn for fn in reader.fieldnames if fn.startswith('modelID=')][0])
                .group('model_id_str'))
            model_schema_number = int(re.match(
                r"modelSchemaNumber=(?P<model_schema_number_str>[0-9]+)",
                [fn for fn in reader.fieldnames if fn.startswith('modelSchemaNumber=')][0])
                .group('model_schema_number_str'))
        except BaseException:
            pass

        # Get form and perform checks:
        if (model_id is not None) and (model_schema_number is not None):
            # Form identification found in CSV header row...
            # Check if this is the right project (with matching model_id):
            if model_id != self.sapelli_model_id:
                raise SapelliCSVException(
                    'modelID mismatch (CSV: %s; project "%s": %s), '
                    'data in CSV file was probably generated using '
                    'another Sapelli project (version).' %
                    (model_id, self.geokey_project.name, self.sapelli_model_id))
            # Get form using model_schema_number:
            try:
                form = self.forms.get(sapelli_model_schema_number=model_schema_number)
            except SapelliForm.DoesNotExist:
                raise SapelliCSVException('No Form with modelSchemaNumber %s found in Project "%s".' % (model_schema_number, self.geokey_project.name))
            # Check if form matches form_category_id given in request:
            if (form_category_id is not None) and form_category_id != form.category.id:
                raise SapelliCSVException('The data in the CSV file was not created using selected form "%s".' % form.sapelli_id)
        elif (form_category_id is not None):
            # No Form identification found in CSV header row, use form_category_id given in request...
            try:
                form = self.forms.get(pk=form_category_id)
            except SapelliForm.DoesNotExist:
                raise SapelliCSVException('No Form with category_id %s found in Project "%s".' % (form_category_id, self.geokey_project.name))
        else:
            # No Form identification found in CSV header row, nor in request...
            raise SapelliCSVException('No Form identification found in CSV header row, please select appropriate form.')

        # Note: only 1 (the first) location field supported:
        location = form.location_fields.all()[0].sapelli_id

        imported = 0
        updated = 0
        ignored_duplicate = 0
        ignored_no_loc = 0

        for row in reader:
            if not row['%s.Longitude' % location]:
                ignored_no_loc += 1
                continue

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

                value = row[sapelli_field.sapelli_id]

                if sapelli_field.truefalse:
                    value = 0 if value == 'false' else 1

                if sapelli_field.items.count() > 0:
                    leaf = sapelli_field.items.get(number=value)
                    value = leaf.lookup_value.id

                feature['properties'][key] = value

            from geokey.contributions.serializers import ContributionSerializer

            try:
                observation = self.geokey_project.observations.get(
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
                        context={'user': user, 'project': self.geokey_project}
                    )

                    if serializer.is_valid(raise_exception=True):
                        serializer.save()

                    updated += 1
                else:
                    ignored_duplicate += 1
            except Observation.DoesNotExist:
                serializer = ContributionSerializer(
                    data=feature,
                    context={'user': user, 'project': self.geokey_project}
                )

                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                imported += 1

        return imported, updated, ignored_duplicate, ignored_no_loc


@receiver(models.signals.post_save, sender=Project)
def post_save_project(sender, instance, **kwargs):
    """
    Receiver that is called after a project is saved. Deletes related Sapelli
    project, when original project is marked as deleted.
    """
    if instance.status == 'deleted':
        try:
            SapelliProject.objects.get(geokey_project=instance).delete()
        except BaseException:
            pass


@receiver(models.signals.pre_delete, sender=Project)
def pre_delete_project(sender, instance, **kwargs):
    """
    Receiver that is called after a project is deleted. Deletes related Sapelli
    project.
    """
    try:
        SapelliProject.objects.get(geokey_project=instance).delete()
    except BaseException:
        pass


class SapelliForm(models.Model):
    """
    Represents a Sapelli form. Is usually created by parsing a Sapelli
    decision tree.
    """
    category = models.OneToOneField(
        'categories.Category',
        primary_key=True,
        related_name='sapelli_form'
    )
    sapelli_project = models.ForeignKey(
        'SapelliProject',
        related_name='forms'
    )
    sapelli_id = models.CharField(max_length=255)
    sapelli_model_schema_number = models.IntegerField(default=-1)


class LocationField(models.Model):
    """
    Represents a Location field.
    """
    sapelli_form = models.ForeignKey(
        'SapelliForm',
        related_name='location_fields'
    )
    sapelli_id = models.CharField(max_length=255)


class SapelliField(models.Model):
    """
    Represents a Sapelli input option, can be a Text input, a list or a choice
    root element.
    """
    sapelli_form = models.ForeignKey(
        'SapelliForm',
        related_name='fields'
    )
    field = models.ForeignKey(
        'categories.Field',
        related_name='sapelli_field'
    )
    sapelli_id = models.CharField(max_length=255)
    truefalse = models.BooleanField(default=False)


class SapelliItem(models.Model):
    """
    Represents a Sapelli Choice element that has no Choice elements as children.
    Is usually created by parsing a Sapelli decision tree.
    """
    lookup_value = models.OneToOneField(
        'categories.LookupValue',
        primary_key=True,
        related_name='sapelli_item'
    )
    number = models.IntegerField()
    sapelli_field = models.ForeignKey(
        'SapelliField',
        related_name='items'
    )


class SAPDownloadQRLink(models.Model):
    """
    Represents a temporary link (embedded in a QR image) that
    allows one to download the SAP file of a SapelliProject.
    The link (or rather the AccessToken it contains) remains valid
    for a default term of 1 day.
    """
    access_token = models.OneToOneField('oauth2_provider.AccessToken', primary_key=True)
    sapelli_project = models.ForeignKey(SapelliProject)

    @classmethod
    def create(cls, user, sapelli_project, days_valid=1):
        """
        Creates and saves a new SAPDownloadQRLink instance.

        Parameter
        ---------
        user : geokey.users.models.User
            User who requests the QR code.
        sapelli_project : SapelliProject:
            The project we want to offer the SAP download link for.
        days_valid : int
            the number of days the link will remain usable.

        Returns
        -------
        SAPDownloadQRLink
            The SAPDownloadQRLink instance

        Raises
        ------
        SapelliException:
            In case of a configuration problem.
        """
        try:
            a_t = AccessToken.objects.create(
                user=user,
                application=Application.objects.get(client_id=settings.SAPELLI_CLIENT_ID),
                expires=timezone.now() + timedelta(days=days_valid),
                token=generate_token(),
                scope='read')
        except (AttributeError, Application.DoesNotExist) as e:
            raise SapelliException('geokey-sapelli is not properly configured as an application on the server: ' + str(e))
        qr_link = cls(access_token=a_t, sapelli_project=sapelli_project)
        qr_link.save()
        return qr_link


@receiver(models.signals.pre_delete, sender=AccessToken)
def pre_delete_access_token(sender, instance, **kwargs):
    """
    Receiver that is called after an AccessToken is deleted. Deletes related SAPDownloadQRLink.
    """
    try:
        SAPDownloadQRLink.objects.get(access_token=instance).delete()
    except BaseException:
        pass
