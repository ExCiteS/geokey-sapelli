# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0010_choice_root_path_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sapelliproject',
            old_name='path',
            new_name='dir_path',
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='sap_path',
            field=models.CharField(max_length=511, null=True),
        ),
    ]
