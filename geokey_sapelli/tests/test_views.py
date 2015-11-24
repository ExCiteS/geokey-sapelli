import json
from os.path import dirname, normpath, abspath, join

from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from django.core.files import File
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.conf import settings

from django.test.client import RequestFactory

from geokey.applications.tests.model_factories import ApplicationFactory
from geokey.users.tests.model_factories import UserF
from geokey.projects.models import Project
from geokey import version

from .model_factories import SapelliProjectFactory, create_full_project

from ..views import ProjectList, ProjectUpload, DataCSVUpload, LoginAPI

from ..helper.dynamic_menu import MenuEntry


class ProjectListTest(TestCase):
    def test_url(self):
        self.assertEqual(reverse('geokey_sapelli:index'), '/admin/sapelli/')

        resolved = resolve('/admin/sapelli/')
        self.assertEqual(resolved.func.func_name, ProjectList.__name__)

    def test_get_with_user(self):
        project = SapelliProjectFactory.create()
        view = ProjectList.as_view()

        request = HttpRequest()
        request.method = 'GET'
        request.user = project.project.creator

        response = view(request).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli_project_list.html',
            {
                'projects': [project],
                'user': project.project.creator,
                'PLATFORM_NAME': get_current_site(request).name,
                'GEOKEY_VERSION': version.get_version(),
                'menu_entries': [
                    MenuEntry(
                        label='Project list',
                        url='geokey_sapelli:index',
                        active=True),
                    MenuEntry(
                        label='Upload new Sapelli project',
                        url='geokey_sapelli:project_upload',
                        active=False)]
            }
        )
        self.assertEqual(unicode(response.content), rendered)

    def test_get_with_anonymous(self):
        view = ProjectList.as_view()
        request = HttpRequest()
        request.method = 'GET'
        request.user = AnonymousUser()
        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')


class ProjectUploadTest(TestCase):
    def setUp(self):
        self.view = ProjectUpload.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'
        self.request.user = AnonymousUser()

        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def test_url(self):
        self.assertEqual(
            reverse('geokey_sapelli:project_upload'),
            '/admin/sapelli/projects/new'
        )

        resolved = resolve('/admin/sapelli/projects/new')
        self.assertEqual(resolved.func.func_name, ProjectUpload.__name__)

    def test_get_with_anonymous(self):
        response = self.view(self.request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')

    def test_get_with_user(self):
        user = UserF.create()
        self.request.user = user

        response = self.view(self.request).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli_upload_project.html',
            {
                'user': user,
                'PLATFORM_NAME': get_current_site(self.request).name,
                'GEOKEY_VERSION': version.get_version(),
                'menu_entries': [
                    MenuEntry(
                        label='Project list',
                        url='geokey_sapelli:index',
                        active=False),
                    MenuEntry(
                        label='Upload new Sapelli project',
                        url='geokey_sapelli:project_upload',
                        active=True)]
            }
        )
        self.assertEqual(unicode(response.content), rendered)

    def test_post_with_anonymous(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {
            'project': file
        }

        response = self.view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')

    def test_post_with_user(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        user = UserF.create()

        self.request.user = user
        self.request.method = 'POST'
        self.request.FILES = {
            'project': file
        }

        response = self.view(self.request)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.first()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['location'], reverse(
                'geokey_sapelli:data_csv_upload',
                kwargs={'project_id': project.id}
            )
        )


class DataCSVUploadTest(TestCase):
    def setUp(self):
        self.user = UserF.create()
        self.view = DataCSVUpload.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'
        self.request.user = AnonymousUser()

        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def test_url(self):
        self.assertEqual(
            reverse(
                'geokey_sapelli:data_csv_upload',
                kwargs={'project_id': 1}
            ),
            '/admin/sapelli/projects/1/csv_upload/'
        )

        resolved = resolve('/admin/sapelli/projects/1/csv_upload/')
        self.assertEqual(resolved.kwargs['project_id'], '1')
        self.assertEqual(resolved.func.func_name, DataCSVUpload.__name__)

    def test_get_with_anonymous(self):
        project = create_full_project(self.user)
        response = self.view(self.request, project_id=project.project_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')

    def test_get_with_user(self):
        project = create_full_project(self.user)
        self.request.user = self.user

        response = self.view(
            self.request,
            project_id=project.project_id).render()

        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli_upload_data_csv.html',
            {
                'sapelli_project': project,
                'user': self.user,
                'PLATFORM_NAME': get_current_site(self.request).name,
                'GEOKEY_VERSION': version.get_version(),
                'menu_entries': [
                    MenuEntry(
                        label='Project list',
                        url='geokey_sapelli:index',
                        active=True),
                    MenuEntry(
                        label='Upload new Sapelli project',
                        url='geokey_sapelli:project_upload',
                        active=False)]
            }
        )
        self.assertEqual(unicode(response.content), rendered)

    def test_post_with_anonymous(self):
        project = create_full_project(self.user)

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {
            'data': file
        }

        response = self.view(self.request, project_id=project.project_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')
        self.assertEqual(project.project.observations.count(), 0)

    def test_post_with_user(self):
        project = create_full_project(self.user)

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {'data': file}
        self.request.POST = {'form_id': project.forms.first().category_id}
        self.request.user = self.user

        response = self.view(
            self.request,
            project_id=project.project_id).render()

        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli_upload_data_csv.html',
            {
                'sapelli_project': project,
                'user': self.user,
                'PLATFORM_NAME': get_current_site(self.request).name,
                'messages': get_messages(self.request),
                'GEOKEY_VERSION': version.get_version(),
                'menu_entries': [
                    MenuEntry(
                        label='Project list',
                        url='geokey_sapelli:index',
                        active=False),
                    MenuEntry(
                        label='Upload new Sapelli project',
                        url='geokey_sapelli:project_upload',
                        active=True)]
            }
        )

        self.assertContains(
            response,
            '4 records have been added to the project'
        )
        self.assertEqual(unicode(response.content), rendered)
        self.assertEqual(project.project.observations.count(), 4)


class LoginAPITest(TestCase):
    def test_url(self):
        self.assertEqual(
            reverse('geokey_sapelli:login_api'),
            '/api/sapelli/login/'
        )

        resolved = resolve('/api/sapelli/login/')
        self.assertEqual(resolved.func.func_name, LoginAPI.__name__)

    def test_post(self):
        user = UserF.create()
        user.set_password('123456')
        user.save()

        ApplicationFactory.create(**{
            'client_id': settings.SAPELLI_CLIENT_ID,
            'authorization_grant_type': 'password'
        })

        data = {
            'username': user.email,
            'password': '123456'
        }

        view = LoginAPI.as_view()
        url = reverse('geokey_sapelli:login_api')

        factory = RequestFactory()
        request = factory.post(url, data)
        response = view(request)

        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('token_type'), 'Bearer')
        self.assertEqual(response_json.get('scope'), 'read write')
        self.assertEqual(response_json.get('expires_in'), 36000)
        self.assertIsNotNone(response_json.get('access_token'))
        self.assertIsNotNone(response_json.get('refresh_token'))
