# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth2_provider', '0002_08_updates'),
        ('geokey_sapelli', '0012_remove_sapelliitem_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='SAPDownloadQRLink',
            fields=[
                ('access_token', models.OneToOneField(primary_key=True, serialize=False, to='oauth2_provider.AccessToken')),
                ('sapelli_project', models.ForeignKey(to='geokey_sapelli.SapelliProject')),
            ],
        ),
    ]
