# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import geokey_sapelli.models


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0009_rename_project_to_geokey_project'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sapelliitem',
            old_name='sapelli_choice_root',
            new_name='sapelli_field',
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='path',
            field=models.CharField(max_length=511, null=True),
        ),
        migrations.AlterField(
            model_name='sapelliitem',
            name='image',
            field=models.ImageField(max_length=500, null=True, upload_to=geokey_sapelli.models.get_img_path),
        ),
    ]
