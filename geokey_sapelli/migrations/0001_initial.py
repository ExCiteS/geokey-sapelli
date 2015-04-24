# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0013_auto_20150130_1440'),
        ('projects', '0005_auto_20150202_1041'),
    ]

    operations = [
        migrations.CreateModel(
            name='SapelliChoice',
            fields=[
                ('lookup_value', models.OneToOneField(related_name='sapelli_choice', primary_key=True, serialize=False, to='categories.LookupValue')),
                ('image', models.ImageField(upload_to=b'sapelli/choice')),
                ('number', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SapelliChoiceRoot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SapelliForm',
            fields=[
                ('category', models.OneToOneField(related_name='sapelli_form', primary_key=True, serialize=False, to='categories.Category')),
                ('sapelli_id', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SapelliProject',
            fields=[
                ('project', models.OneToOneField(related_name='sapelli_project', primary_key=True, serialize=False, to='projects.Project')),
                ('sapelli_id', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='sapelliform',
            name='sapelli_project',
            field=models.ForeignKey(related_name='forms', to='geokey_sapelli.SapelliProject'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sapellichoiceroot',
            name='sapelli_form',
            field=models.ForeignKey(related_name='choices', to='geokey_sapelli.SapelliForm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sapellichoiceroot',
            name='select_field',
            field=models.ForeignKey(related_name='sapelli_choice_root', to='categories.LookupField'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sapellichoice',
            name='sapelli_choice_root',
            field=models.ForeignKey(related_name='choices_leafs', to='geokey_sapelli.SapelliChoiceRoot'),
            preserve_default=True,
        ),
    ]
