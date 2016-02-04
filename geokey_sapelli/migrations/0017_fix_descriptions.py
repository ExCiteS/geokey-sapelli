# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def fix_description(instance):
    if instance.description is None:
        instance.description = ''
        instance.save()


def check_descriptions(apps, schema_editor):
    SapelliForm = apps.get_model('geokey_sapelli', 'SapelliForm')
    SapelliField = apps.get_model('geokey_sapelli', 'SapelliField')

    for sapelli_form in SapelliForm.objects.all():
        fix_description(sapelli_form.category)

    for sapelli_field in SapelliField.objects.all():
        fix_description(sapelli_field.field)


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0016_fix_old_sapelli_projects'),
    ]

    operations = [
        migrations.RunPython(check_descriptions),
    ]
