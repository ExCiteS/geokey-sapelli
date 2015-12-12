from os.path import dirname, normpath, abspath, join

from django.core.files import File
from django.test import TestCase

from geokey.users.tests.model_factories import UserFactory
from geokey.projects.models import Project
from geokey.projects.tests.model_factories import ProjectFactory

from ..models import SapelliProject, post_save_project, pre_delete_project
from .model_factories import SapelliProjectFactory, create_full_project


class SapelliProjectTest(TestCase):

    def test_import_from_csv(self):

        user = UserFactory.create()
        sapelli_project = create_full_project(user)

        form = sapelli_project.forms.all()[0]

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        imported, updated, ignored_dup, ignored_no_loc = sapelli_project.import_from_csv(
            user,
            form.category_id,
            file
        )
        self.assertEqual(imported, 4)
        self.assertEqual(updated, 0)
        self.assertEqual(ignored_dup, 0)
        self.assertEqual(ignored_no_loc, 1)
        self.assertEqual(sapelli_project.project.observations.count(), 4)

        path = normpath(join(dirname(abspath(__file__)), 'files/updated.csv'))
        file = File(open(path, 'rb'))
        imported, updated, ignored_dup, ignored_no_loc = sapelli_project.import_from_csv(
            user,
            form.category_id,
            file
        )
        self.assertEqual(imported, 1)
        self.assertEqual(updated, 2)
        self.assertEqual(ignored_dup, 1)
        self.assertEqual(ignored_no_loc, 0)
        self.assertEqual(sapelli_project.project.observations.count(), 5)


class ProjectSaveTest(TestCase):

    def test_post_save_when_project_made_deleted(self):

        project = ProjectFactory.create(status='active')
        sapelli_project = SapelliProjectFactory.create(project=project)

        project.status = 'deleted'
        project.save

        post_save_project(Project, instance=project)

        self.assertEqual(
            SapelliProject.objects.filter(pk=sapelli_project.pk).exists(),
            False
        )


class ProjectDeleteTest(TestCase):

    def test_pre_delete_project(self):

        project = ProjectFactory.create(status='active')
        sapelli_project = SapelliProjectFactory.create(project=project)

        pre_delete_project(Project, instance=project)

        self.assertEqual(
            SapelliProject.objects.filter(pk=sapelli_project.pk).exists(),
            False
        )
