# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0013_auto_20150130_1440'),
        ('geokey_sapelli', '0002_sapellichoiceroot_sapelli_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='SapelliField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sapelli_id', models.CharField(max_length=255)),
                ('field', models.ForeignKey(related_name='sapelli_field', to='categories.Field')),
                ('sapelli_form', models.ForeignKey(related_name='fields', to='geokey_sapelli.SapelliForm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SapelliItem',
            fields=[
                ('lookup_value', models.OneToOneField(related_name='sapelli_item', primary_key=True, serialize=False, to='categories.LookupValue')),
                ('image', models.ImageField(null=True, upload_to=b'sapelli/item')),
                ('number', models.IntegerField()),
                ('sapelli_choice_root', models.ForeignKey(related_name='items', to='geokey_sapelli.SapelliField')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='sapellichoice',
            name='lookup_value',
        ),
        migrations.RemoveField(
            model_name='sapellichoice',
            name='sapelli_choice_root',
        ),
        migrations.DeleteModel(
            name='SapelliChoice',
        ),
        migrations.RemoveField(
            model_name='sapellichoiceroot',
            name='sapelli_form',
        ),
        migrations.RemoveField(
            model_name='sapellichoiceroot',
            name='select_field',
        ),
        migrations.DeleteModel(
            name='SapelliChoiceRoot',
        ),
    ]
