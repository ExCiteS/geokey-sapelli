# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import geokey_sapelli.models


def get_img_path(instance, filename):
    if filename is None or instance.sapelli_field.sapelli_form.sapelli_project.dir_path is None:
        return None
    else:
        return os.path.join(instance.sapelli_field.sapelli_form.sapelli_project.dir_path, 'img/', filename)


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
            field=models.ImageField(max_length=500, null=True, upload_to=get_img_path),
        ),
    ]
