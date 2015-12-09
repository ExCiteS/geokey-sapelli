from django.test import TestCase

from geokey.users.tests.model_factories import UserFactory
from geokey.projects.tests.model_factories import ProjectFactory

from .model_factories import SapelliProjectFactory

from ..models import SapelliProject


class SapelliManagerTest(TestCase):
    def test_get_list_for_administration(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_admins=[user])

        admin_sap_project = SapelliProjectFactory.create(
            **{'project': project}
        )
        SapelliProjectFactory.create_batch(2)

        sap_projects = SapelliProject.objects.get_list_for_administration(user)
        self.assertEqual(1, sap_projects.count())
        self.assertEqual(sap_projects[0], admin_sap_project)

    def test_get_list_for_contribution(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_contributors=[user])

        contrib_sap_project = SapelliProjectFactory.create(
            **{'project': project}
        )
        SapelliProjectFactory.create_batch(2)

        sap_projects = SapelliProject.objects.get_list_for_contribution(user)
        self.assertEqual(1, len(sap_projects))
        self.assertEqual(sap_projects[0], contrib_sap_project)

    def test_get_single_for_administration(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_admins=[user])

        admin_sap_project = SapelliProjectFactory.create(
            **{'project': project}
        )
        other_sap_project = SapelliProjectFactory.create()

        ref = SapelliProject.objects.get_single_for_administration(
            user, admin_sap_project.project_id)
        self.assertEqual(ref, admin_sap_project)

        try:
            SapelliProject.objects.get_single_for_administration(
                user,
                other_sap_project.project_id
            )
        except SapelliProject.DoesNotExist:
            pass
        else:
            self.fail('SapelliProject.DoesNotExist not raised')

    def test_get_single_for_contribution(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_contributors=[user])

        contrib_sap_project = SapelliProjectFactory.create(
            **{'project': project}
        )
        other_sap_project = SapelliProjectFactory.create()

        ref = SapelliProject.objects.get_single_for_contribution(
            user, contrib_sap_project.project_id)
        self.assertEqual(ref, contrib_sap_project)

        try:
            SapelliProject.objects.get_single_for_contribution(
                user,
                other_sap_project.project_id
            )
        except SapelliProject.DoesNotExist:
            pass
        else:
            self.fail('SapelliProject.DoesNotExist not raised')
