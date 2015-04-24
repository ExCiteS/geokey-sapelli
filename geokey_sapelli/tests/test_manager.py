from django.test import TestCase

from geokey.users.tests.model_factories import UserF
from geokey.projects.tests.model_factories import ProjectF

from .model_factories import SapelliProjectFactory

from ..models import SapelliProject


class SapelliManagerTest(TestCase):
    def test_get_list(self):
        user = UserF.create()
        project = ProjectF.create(add_admins=[user])

        admin_project = SapelliProjectFactory.create(**{'project': project})
        SapelliProjectFactory.create_batch(2)

        projects = SapelliProject.objects.get_list(user)
        self.assertEqual(1, projects.count())
        self.assertEqual(projects[0], admin_project)

    def test_get_single(self):
        user = UserF.create()
        project = ProjectF.create(add_admins=[user])

        admin_project = SapelliProjectFactory.create(**{'project': project})
        other_project = SapelliProjectFactory.create()

        ref = SapelliProject.objects.get_single(
            user, admin_project.project_id)
        self.assertEqual(ref, admin_project)

        try:
            SapelliProject.objects.get_single(user, other_project.project_id)
        except SapelliProject.DoesNotExist:
            pass
        else:
            self.fail('SapelliProject.DoesNotExist not raised')
