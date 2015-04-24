from os.path import dirname, normpath, abspath, join

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files import File

from geokey.users.tests.model_factories import UserF
from geokey.projects.models import Project

from .model_factories import SapelliProjectFactory, create_full_project


class ProjectListTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('geokey_sapelli:index')

    def test_get_with_user(self):
        project = SapelliProjectFactory.create()
        user = project.project.creator
        user.set_password('123456')
        user.save()

        self.client.login(username=user.email, password='123456')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['projects']), 1)

    def test_get_with_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/admin/account/login/?next=%s' % self.url)


class ProjectUploadTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_with_anonymous(self):
        url = reverse('geokey_sapelli:project_upload')
        response = self.client.get(url)
        self.assertRedirects(response, '/admin/account/login/?next=%s' % url)

    def test_get_with_user(self):
        user = UserF.create(**{'password': '123456'})
        url = reverse('geokey_sapelli:project_upload')
        self.client.login(username=user.email, password='123456')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_with_anonymous(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        data = {
            'project': file
        }
        url = reverse('geokey_sapelli:project_upload')
        response = self.client.post(url, data)
        self.assertRedirects(response, '/admin/account/login/?next=%s' % url)

    def test_post_with_user(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        data = {
            'project': file
        }

        user = UserF.create(**{'password': '123456'})
        url = reverse('geokey_sapelli:project_upload')
        self.client.login(username=user.email, password='123456')
        response = self.client.post(url, data)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.all()[0]

        self.assertRedirects(
            response, 'admin/sapelli/projects/%s/upload/' % project.id)


class DataUploadTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = UserF.create()
        self.user.set_password('123456')
        self.user.save()

        self.project = create_full_project(self.user)
        self.url = reverse(
            'geokey_sapelli:data_upload',
            kwargs={'project_id': self.project.project.id}
        )

    def test_get_with_anonymous(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response, '/admin/account/login/?next=%s' % self.url)

    def test_get_with_user(self):
        self.client.login(username=self.user.email, password='123456')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_with_anonymous(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        data = {
            'data': file
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(
            response, '/admin/account/login/?next=%s' % self.url)

        self.assertEqual(self.project.project.observations.count(), 0)

    def test_post_with_user(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))
        data = {
            'data': file,
            'form_id': self.project.forms.all()[0].category_id
        }
        self.client.login(username=self.user.email, password='123456')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.project.project.observations.count(), 4)
