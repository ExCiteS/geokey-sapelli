# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def copy_image_to_lookup_field(apps, schema_editor):
    SapelliItem = apps.get_model('geokey_sapelli', 'SapelliItem')
    for si in SapelliItem.objects.all():
        si.lookup_value.symbol = si.image
        si.lookup_value.save()

class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0011_dir_path_sap_path'),
        ('categories', '0015_lookupvalue_symbol'),
    ]

    operations = [
        migrations.RunPython(copy_image_to_lookup_field),

        migrations.RemoveField(
            model_name='sapelliitem',
            name='image',
        ),
    ]
