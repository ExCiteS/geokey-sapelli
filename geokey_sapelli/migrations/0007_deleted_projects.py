# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def check_projects(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    SapelliProject = apps.get_model('geokey_sapelli', 'SapelliProject')

    for sapelli_project in SapelliProject.objects.all():
        try:
            project = Project.objects.get(pk=sapelli_project.project.id)

            if project.status == 'deleted':
                sapelli_project.delete()
        except Project.DoesNotExist:
            sapelli_project.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0006_sapelliproject_sapelli_fingerprint'),
    ]

    operations = [
        migrations.RunPython(check_projects),
    ]
