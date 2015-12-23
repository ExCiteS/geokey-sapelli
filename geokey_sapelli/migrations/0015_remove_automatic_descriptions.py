# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def remove_automatic_descriptions(apps, schema_editor):
    SapelliProject = apps.get_model('geokey_sapelli', 'SapelliProject')
    for sapelli_project in SapelliProject.objects.all():
        auto_descr = 'Sapelli project id: %s;\nSapelli project fingerprint: %s;' % (
            sapelli_project.sapelli_id,
            sapelli_project.sapelli_fingerprint)
        if sapelli_project.geokey_project.description == auto_descr:
            sapelli_project.geokey_project.description = ''
            sapelli_project.geokey_project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0014_fix_everyone_contributes'),
    ]
    
    operations = [
        migrations.RunPython(remove_automatic_descriptions),
    ]
