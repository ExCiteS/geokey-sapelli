# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from geokey.projects.base import EVERYONE_CONTRIBUTES


def fix_everyone_contributes(apps, schema_editor):
    SapelliProject = apps.get_model('geokey_sapelli', 'SapelliProject')
    for sapelli_project in SapelliProject.objects.all():
        if sapelli_project.geokey_project.everyone_contributes == u'False':
            sapelli_project.geokey_project.everyone_contributes = EVERYONE_CONTRIBUTES.false
            sapelli_project.geokey_project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0013_sapdownloadqrlink'),
    ]

    operations = [
        migrations.RunPython(fix_everyone_contributes),
    ]
