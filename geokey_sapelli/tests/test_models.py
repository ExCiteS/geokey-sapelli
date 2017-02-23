from os.path import dirname, normpath, abspath, join

from django.core.files import File
from django.test import TestCase

from geokey.users.tests.model_factories import UserFactory
from geokey.projects.models import Project
from geokey.projects.tests.model_factories import ProjectFactory

from ..models import SapelliProject, post_save_project, pre_delete_project, SAPDownloadQRLink
from .model_factories import SapelliProjectFactory, create_horniman_sapelli_project, create_textunicode_sapelli_project, GeoKeySapelliApplicationFactory

from ..helper.sapelli_exceptions import SapelliCSVException


class SapelliProjectTest(TestCase):

    def test_import_from_csv_horniman_correct(self):
        user = UserFactory.create()
        sapelli_project = create_horniman_sapelli_project(user)

        form = sapelli_project.forms.all()[0]

        # Import records (4 with loc, 1 without):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        imported, imported_joined_locs, imported_no_loc, updated, ignored_dup = sapelli_project.import_from_csv(
            user,
            file,
            form.category_id
        )
        self.assertEqual(imported, 4)
        self.assertEqual(imported_joined_locs, 0)
        self.assertEqual(imported_no_loc, 1)
        self.assertEqual(updated, 0)
        self.assertEqual(ignored_dup, 0)
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 5)

        # Some more records (1 new, 2 updated, 1 duplicate), without user-selected form:
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman_updated.csv'))
        file = File(open(path, 'rb'))
        imported, imported_joined_locs, imported_no_loc, updated, ignored_dup = sapelli_project.import_from_csv(
            user,
            file
            # no form.category_id given!
        )
        self.assertEqual(imported, 1)
        self.assertEqual(imported_joined_locs, 0)
        self.assertEqual(imported_no_loc, 0)
        self.assertEqual(updated, 2)
        self.assertEqual(ignored_dup, 1)
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 6)

        # Process CSV without form identification info in header, with user-selected form:
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman_updated_no_form_ident.csv'))
        file = File(open(path, 'rb'))
        imported, imported_joined_locs, imported_no_loc, updated, ignored_dup = sapelli_project.import_from_csv(
            user,
            file,
            form.category_id
        )
        self.assertEqual(imported, 1)
        self.assertEqual(imported_joined_locs, 0)
        self.assertEqual(imported_no_loc, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(ignored_dup, 0)
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 7)

    def test_import_from_csv_horniman_corrupt(self):
        user = UserFactory.create()
        sapelli_project = create_horniman_sapelli_project(user)

        form = sapelli_project.forms.all()[0]

        # Call import with an invalid form_category_id (must fail):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        self.assertRaises(SapelliCSVException, sapelli_project.import_from_csv,
            user,
            file,
            form.category_id + 1  # invalid!
        )
        # Process CSV without form identification info in header, without user-selected form (must fail):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman_updated_no_form_ident.csv'))
        file = File(open(path, 'rb'))
        self.assertRaises(SapelliCSVException, sapelli_project.import_from_csv,
            user,
            file
            # no form.category_id given!
        )

    def test_import_from_csv_texttest_unicode(self):
        user = UserFactory.create()
        sapelli_project = create_textunicode_sapelli_project(user)

        form = sapelli_project.forms.all()[0]

        # Import records with unicode characters:
        path = normpath(join(dirname(abspath(__file__)), 'files/TextUnicode.csv'))
        file = File(open(path, 'rb'))
        imported, imported_joined_locs, imported_no_loc, updated, ignored_dup = sapelli_project.import_from_csv(
            user,
            file,
            form.category_id
        )
        self.assertEqual(imported, 2)
        self.assertEqual(imported_joined_locs, 0)
        self.assertEqual(imported_no_loc, 0)
        self.assertEqual(updated, 0)
        self.assertEqual(ignored_dup, 0)
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 2)

        observation = sapelli_project.geokey_project.observations.get(
            category_id=form.category.id,
            properties__at_StartTime='2015-12-12T06:23:04.570-05:00')
        self.assertEqual(observation.properties['txttext'], u'\ud55c\uc790test')


class ProjectSaveTest(TestCase):
    def test_post_save_when_project_made_deleted(self):
        geokey_project = ProjectFactory.create(status='active')
        sapelli_project = SapelliProjectFactory.create(geokey_project=geokey_project)

        geokey_project.status = 'deleted'
        geokey_project.save

        post_save_project(Project, instance=geokey_project)

        self.assertFalse(SapelliProject.objects.filter(pk=sapelli_project.pk).exists())


class ProjectDeleteTest(TestCase):
    def test_pre_delete_project(self):
        geokey_project = ProjectFactory.create(status='active')
        sapelli_project = SapelliProjectFactory.create(geokey_project=geokey_project)

        pre_delete_project(Project, instance=geokey_project)

        self.assertFalse(SapelliProject.objects.filter(pk=sapelli_project.pk).exists())


class SAPDownloadQRLinkTest(TestCase):
    def setUp(self):
        self.app = GeoKeySapelliApplicationFactory.create()
        self.user = UserFactory.create()
        self.user.set_password('123456')
        self.user.save()

    def tearDown(self):
        try:
            self.sap_download_qr_link.delete()
            self.app.delete()
            self.user.delete()
        except BaseException:
            pass

    def test_create_qr_link(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        self.sap_download_qr_link = SAPDownloadQRLink.create(user=self.user, sapelli_project=sapelli_project, days_valid=1)

        self.assertEqual(self.sap_download_qr_link.access_token.user, self.user)
        self.assertEqual(self.sap_download_qr_link.access_token.application, self.app)
        self.assertEqual(self.sap_download_qr_link.sapelli_project, sapelli_project)

