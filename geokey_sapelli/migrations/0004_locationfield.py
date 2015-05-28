# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0003_auto_20150512_1533'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocationField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sapelli_id', models.CharField(max_length=255)),
                ('sapelli_form', models.ForeignKey(related_name='location_fields', to='geokey_sapelli.SapelliForm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
