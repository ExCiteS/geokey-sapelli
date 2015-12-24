# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_missing_field_values(apps, schema_editor):
    SapelliProject = apps.get_model('geokey_sapelli', 'SapelliProject')
    for sapelli_project in SapelliProject.objects.all():
        # set missing values:
        if sapelli_project.name == '':
            sapelli_project.name = sapelli_project.geokey_project.name
            sapelli_project.save()
        if sapelli_project.sapelli_model_id == -1:
            # see: https://github.com/ExCiteS/Sapelli/blob/master/Library/src/uk/ac/ucl/excites/sapelli/collector/CollectorClient.java
            sapelli_project.sapelli_model_id = ((sapelli_project.sapelli_fingerprint & 0xffffffffl) << 24) + sapelli_project.sapelli_id
            sapelli_project.save()
        # set missing sapelli_model_schema_number values on forms:
        if sapelli_project.forms.values():
            min_category_id = min(map(lambda (f): f['category_id'], sapelli_project.forms.values()))
            for form in sapelli_project.forms.all():
                if form.sapelli_model_schema_number == -1:
                    form.sapelli_model_schema_number = form.category.id - min_category_id + 1 #(due to Heartbeat Schema)
                    form.save()

class Migration(migrations.Migration):

    dependencies = [
        ('geokey_sapelli', '0015_remove_automatic_descriptions'),
    ]
    
    operations = [
        migrations.RunPython(set_missing_field_values),
    ]
