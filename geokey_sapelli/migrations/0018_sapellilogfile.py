# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geokey_sapelli', '0017_fix_descriptions'),
    ]

    operations = [
        migrations.CreateModel(
            name='SapelliLogFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('file', models.FileField(upload_to=b'sapelli/logs/%Y/%m/%d/')),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('sapelli_project', models.ForeignKey(related_name='logs', to='geokey_sapelli.SapelliProject')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
    ]
