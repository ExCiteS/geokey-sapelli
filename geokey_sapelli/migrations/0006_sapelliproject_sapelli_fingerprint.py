# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0005_sapellifield_truefalse'),
    ]

    operations = [
        migrations.AddField(
            model_name='sapelliproject',
            name='sapelli_fingerprint',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
    ]
