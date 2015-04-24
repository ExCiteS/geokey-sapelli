from os.path import dirname, normpath, abspath, join

from django.core.files import File
from django.test import TestCase

from geokey.users.tests.model_factories import UserF

from .model_factories import create_full_project


class ProjectTest(TestCase):
    def test_import_from_csv(self):
        user = UserF.create()
        sapelli_project = create_full_project(user)

        form = sapelli_project.forms.all()[0]

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        number = sapelli_project.import_from_csv(user, form.category_id, file)
        self.assertEqual(number, 4)
        self.assertEqual(sapelli_project.project.observations.count(), 4)
