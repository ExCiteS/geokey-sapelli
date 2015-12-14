# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0008_additional_project_and_form_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sapelliproject',
            old_name='project',
            new_name='geokey_project',
        ),
    ]
