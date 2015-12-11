from os.path import dirname, normpath, abspath, join

from django.core.files import File
from django.test import TestCase

from geokey.users.tests.model_factories import UserFactory

from .model_factories import create_full_project


class ProjectTest(TestCase):
    def test_import_from_csv(self):
        user = UserFactory.create()
        sapelli_project = create_full_project(user)

        form = sapelli_project.forms.all()[0]

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        imported, updated, ignored = sapelli_project.import_from_csv(
            user,
            form.category_id,
            file
        )
        self.assertEqual(imported, 4)
        self.assertEqual(updated, 0)
        self.assertEqual(ignored, 0)
        self.assertEqual(sapelli_project.project.observations.count(), 4)

        path = normpath(join(dirname(abspath(__file__)), 'files/updated.csv'))
        file = File(open(path, 'rb'))
        imported, updated, ignored = sapelli_project.import_from_csv(
            user,
            form.category_id,
            file
        )
        self.assertEqual(imported, 1)
        self.assertEqual(updated, 2)
        self.assertEqual(ignored, 1)
        self.assertEqual(sapelli_project.project.observations.count(), 5)
