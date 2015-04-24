# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sapellichoiceroot',
            name='sapelli_id',
            field=models.CharField(default='Blah', max_length=255),
            preserve_default=False,
        ),
    ]
