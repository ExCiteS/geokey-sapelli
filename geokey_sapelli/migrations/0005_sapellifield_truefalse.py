# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0004_locationfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='sapellifield',
            name='truefalse',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
