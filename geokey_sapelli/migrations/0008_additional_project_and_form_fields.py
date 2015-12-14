# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0007_deleted_projects'),
    ]

    operations = [
        migrations.AddField(
            model_name='sapelliform',
            name='sapelli_model_schema_number',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='name',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='sapelli_model_id',
            field=models.BigIntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='variant',
            field=models.CharField(max_length=63, null=True),
        ),
        migrations.AddField(
            model_name='sapelliproject',
            name='version',
            field=models.CharField(default=b'0', max_length=63),
        ),
    ]
