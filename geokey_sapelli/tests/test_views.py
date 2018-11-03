# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from os.path import dirname, normpath, abspath, join
from datetime import datetime
from pytz import utc

from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from django.core.files import File
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage

from django.test.client import RequestFactory

from oauth2_provider.models import AccessToken

from rest_framework.test import APIRequestFactory, force_authenticate

from geokey import version
from geokey.core.tests.helpers import render_helpers
from geokey.users.tests.model_factories import UserFactory
from geokey.projects.models import Project
from geokey.projects.tests.model_factories import ProjectFactory

from .model_factories import (
    GeoKeySapelliApplicationFactory,
    SapelliProjectFactory,
    create_horniman_sapelli_project, create_qr_link,
)
from .test_helpers import get_log_file
from ..models import (
    SapelliProject,
    SAPDownloadQRLink,
    SapelliLogFile,
)
from ..views import (
    ProjectList,
    ProjectUpload,
    DataCSVUpload,
    DataLogsDownload,
    LoginAPI,
    SAPDownloadAPI,
    SAPDownloadQRLinkAPI,
    SapelliLogsViaPersonalInfo,
    SapelliLogsViaGeoKeyInfo,
)


class ProjectListTest(TestCase):
    def setUp(self):
        self.view = ProjectList.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'

        setattr(self.request, 'session', 'session')
        setattr(self.request, '_messages', FallbackStorage(self.request))

    def test_url(self):
        self.assertEqual(reverse('geokey_sapelli:index'), '/admin/sapelli/')

        resolved = resolve('/admin/sapelli/')
        self.assertEqual(resolved.func.func_name, ProjectList.__name__)

    def test_get_with_user(self):
        sapelli_project = SapelliProjectFactory.create()
        self.request.user = sapelli_project.geokey_project.creator

        response = self.view(self.request).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/index.html',
            {
                'GEOKEY_VERSION': version.get_version(),
                'PLATFORM_NAME': get_current_site(self.request).name,
                'messages': get_messages(self.request),
                'user': sapelli_project.geokey_project.creator,
                'sapelli_projects': [sapelli_project],
            }
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)

    def test_get_with_anonymous(self):
        self.request.user = AnonymousUser()
        response = self.view(self.request)

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

    def tearDown(self):
        # delete project(s):
        for sapelli_project in SapelliProject.objects.filter(sapelli_id=1111):
            try:
                sapelli_project.geokey_project.delete()  # will also delete sapelli_project
            except BaseException:
                pass

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
        user = UserFactory.create()
        self.request.user = user

        response = self.view(self.request).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/upload_sapelli_project.html',
            {
                'GEOKEY_VERSION': version.get_version(),
                'PLATFORM_NAME': get_current_site(self.request).name,
                'user': user,
            }
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)

    def test_post_with_anonymous(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {
            'sap_file': file
        }

        response = self.view(self.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')
        self.assertEqual(Project.objects.count(), 0)

    def test_post_with_user(self):
        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.sap'))
        file = File(open(path, 'rb'))
        user = UserFactory.create()

        self.request.user = user
        self.request.method = 'POST'
        self.request.FILES = {
            'sap_file': file
        }

        response = self.view(self.request)
        self.assertEqual(Project.objects.count(), 1)
        geokey_project = Project.objects.first()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['location'], reverse(
                'geokey_sapelli:data_csv_upload',
                kwargs={'project_id': geokey_project.id}
            )
        )
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(geokey_project.islocked, True)


class DataCSVUploadTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.view = DataCSVUpload.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'
        self.request.user = AnonymousUser()

        setattr(self.request, 'session', 'session')
        setattr(self.request, '_messages', FallbackStorage(self.request))

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
        sapelli_project = create_horniman_sapelli_project(self.user)
        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')

    def test_get_with_user(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        self.request.user = self.user

        response = self.view(
            self.request,
            project_id=sapelli_project.geokey_project.id).render()

        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/upload_data_csv.html',
            {
                'GEOKEY_VERSION': version.get_version(),
                'PLATFORM_NAME': get_current_site(self.request).name,
                'user': self.user,
                'sapelli_project': sapelli_project,
            }
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)

    def test_post_with_anonymous(self):
        sapelli_project = create_horniman_sapelli_project(self.user)

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {
            'csv_file': file
        }

        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 0)

    def test_post_with_user(self):
        sapelli_project = create_horniman_sapelli_project(self.user)

        path = normpath(join(dirname(abspath(__file__)), 'files/Horniman.csv'))
        file = File(open(path, 'rb'))

        self.request.method = 'POST'
        self.request.FILES = {'csv_file': file}
        self.request.POST = {'form_category_id': sapelli_project.forms.first().category_id}
        self.request.user = self.user

        response = self.view(
            self.request,
            project_id=sapelli_project.geokey_project.id).render()

        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/upload_data_csv.html',
            {
                'GEOKEY_VERSION': version.get_version(),
                'PLATFORM_NAME': get_current_site(self.request).name,
                'messages': get_messages(self.request),
                'user': self.user,
                'sapelli_project': sapelli_project,
            }
        )

        self.assertContains(
            response,
            '4 records have been added as project contributions'
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)
        self.assertEqual(sapelli_project.geokey_project.observations.count(), 5)


class DataLogsDownloadTest(TestCase):
    """Test page for data logs download."""

    def setUp(self):
        """Set up test."""
        self.admin = UserFactory.create()
        self.regular_user = UserFactory.create()
        self.anonymous_user = AnonymousUser()
        self.sapelli_project = create_horniman_sapelli_project(self.admin)

        self.view = DataLogsDownload.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'

        setattr(self.request, 'session', 'session')
        setattr(self.request, '_messages', FallbackStorage(self.request))

    def test_url(self):
        """Test URL."""
        self.assertEqual(
            reverse(
                'geokey_sapelli:logs',
                kwargs={'project_id': 1}
            ),
            '/admin/sapelli/projects/1/logs/')

        resolved = resolve('/admin/sapelli/projects/1/logs/')
        self.assertEqual(resolved.kwargs['project_id'], '1')
        self.assertEqual(resolved.func.func_name, DataLogsDownload.__name__)

    def test_get_with_anonymous_user(self):
        """Test GET with anonymous user."""
        self.request.user = self.anonymous_user
        response = self.view(
            self.request,
            project_id=self.sapelli_project.geokey_project.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/admin/account/login/?next=')

    def test_get_with_regular_user(self):
        """Test GET with regular user."""
        self.request.user = self.regular_user
        response = self.view(
            self.request,
            project_id=self.sapelli_project.geokey_project.id).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/logs.html',
            {
                'PLATFORM_NAME': get_current_site(self.request).name,
                'GEOKEY_VERSION': version.get_version(),
                'user': self.request.user,
                'error': 'Not found',
                'error_description': 'Sapelli project not found.',
            }
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)

    def test_get_with_admin(self):
        """Test GET with admin."""
        self.request.user = self.admin
        response = self.view(
            self.request,
            project_id=self.sapelli_project.geokey_project.id).render()
        self.assertEqual(response.status_code, 200)

        rendered = render_to_string(
            'sapelli/logs.html',
            {
                'PLATFORM_NAME': get_current_site(self.request).name,
                'GEOKEY_VERSION': version.get_version(),
                'user': self.request.user,
                'sapelli_project': self.sapelli_project,
            }
        )
        response = render_helpers.remove_csrf(response.content.decode('utf-8'))
        self.assertEqual(response, rendered)


class LoginAPITest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.user.set_password('123456')
        self.user.save()
        self.app = GeoKeySapelliApplicationFactory.create()

    def tearDown(self):
        self.user.delete()
        self.app.delete()

    def test_url(self):
        self.assertEqual(
            reverse('geokey_sapelli:login_api'),
            '/api/sapelli/login/'
        )

        resolved = resolve('/api/sapelli/login/')
        self.assertEqual(resolved.func.func_name, LoginAPI.__name__)

    def test_post(self):
        data = {
            'username': self.user.email,
            'password': '123456'
        }

        view = LoginAPI.as_view()
        url = reverse('geokey_sapelli:login_api')

        factory = RequestFactory()
        request = factory.post(url, data)
        response = view(request)
        response.render()

        response_json = json.loads(response.content)
        self.assertEqual(response_json.get('token_type'), 'Bearer')
        self.assertEqual(response_json.get('scope'), 'read write')
        self.assertEqual(response_json.get('expires_in'), 36000)
        self.assertIsNotNone(response_json.get('expires_at'))
        self.assertIsNotNone(response_json.get('access_token'))
        self.assertIsNotNone(response_json.get('refresh_token'))

    def test_get_with_anonymous(self):
        view = LoginAPI.as_view()
        url = reverse('geokey_sapelli:login_api')

        request = HttpRequest()
        request.method = 'GET'
        request.user = AnonymousUser()
        response = view(request)
        response.render()

        response_json = json.loads(response.content)
        self.assertFalse(response_json.get('logged_in'))

    def test_get_with_user(self):
        view = LoginAPI.as_view()
        url = reverse('geokey_sapelli:login_api')

        request = HttpRequest()
        request.method = 'GET'
        request.user = self.user
        response = view(request)
        response.render()

        response_json = json.loads(response.content)
        self.assertTrue(response_json.get('logged_in'))


class SAPDownloadAPITest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.view = SAPDownloadAPI.as_view()
        self.request = HttpRequest()
        self.request.method = 'GET'
        self.request.user = AnonymousUser()

    def test_url(self):
        self.assertEqual(
            reverse(
                'geokey_sapelli:sap_download_api',
                kwargs={'project_id': 1}
            ),
            '/api/sapelli/projects/1/sap/'
        )
        resolved = resolve('/api/sapelli/projects/1/sap/')
        self.assertEqual(resolved.kwargs['project_id'], '1')
        self.assertEqual(resolved.func.func_name, SAPDownloadAPI.__name__)

    def test_get_with_anonymous(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)
        self.assertEqual(response.status_code, 403)

    def test_get_with_user(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        self.request.user = self.user

        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')


class SAPDownloadQRLinkAPITest(TestCase):
    def setUp(self):
        self.app = GeoKeySapelliApplicationFactory.create()

        self.user = UserFactory.create()
        self.user.set_password('123456')
        self.user.save()

        self.view = SAPDownloadQRLinkAPI.as_view()

        self.request = HttpRequest()
        self.request.method = 'GET'
        # necessary for request.build_absolute_uri() to work:
        self.request.META['SERVER_NAME'] = 'test-server'
        self.request.META['SERVER_PORT'] = '80'

    def tearDown(self):
        # delete tokens:
        for access_token in AccessToken.objects.filter(user=self.user):
            access_token.delete()
        # delete app:
        self.app.delete()
        # delete user:
        self.user.delete()

    def test_url(self):
        self.assertEqual(
            reverse(
                'geokey_sapelli:sap_download_qr_link_api',
                kwargs={'project_id': 1}
            ),
            '/api/sapelli/projects/1/sap_qr_link.png'
        )
        resolved = resolve('/api/sapelli/projects/1/sap_qr_link.png')
        self.assertEqual(resolved.kwargs['project_id'], '1')
        self.assertEqual(resolved.func.func_name, SAPDownloadQRLinkAPI.__name__)

    def test_get_with_anonymous(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        self.request.user = AnonymousUser()

        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)
        self.assertEqual(response.status_code, 403)

    def test_get_with_user(self):
        sapelli_project = create_horniman_sapelli_project(self.user)
        self.request.user = self.user

        response = self.view(self.request, project_id=sapelli_project.geokey_project.id)

        qr_link = SAPDownloadQRLink.objects.filter(access_token__user=self.user, sapelli_project=sapelli_project).latest('access_token__expires')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['X-QR-Access-Token'], qr_link.access_token.token)
        self.assertEqual(response['X-QR-Access-Token-Expires'], qr_link.access_token.expires.isoformat())

    def test_delete_with_user(self):
        delete_request = HttpRequest()
        delete_request.method = 'DELETE'
        delete_request.user = self.user
        force_authenticate(delete_request, user=self.user)

        sapelli_project = create_horniman_sapelli_project(self.user)
        qr_link = create_qr_link(self.app, self.user, sapelli_project)

        response = self.view(delete_request, project_id=sapelli_project.geokey_project.id).render()
        response_json = json.loads(response.content)

        self.assertTrue(response_json.get('deleted'))
        self.assertNotIn(qr_link, SAPDownloadQRLink.objects.all())


class SapelliLogsViaPersonalInfoTest(TestCase):
    """Test public API for Sapelli logs via the personal (GeoKey) info."""

    def setUp(self):
        """Set up test."""
        self.factory = APIRequestFactory()
        self.admin = UserFactory.create()
        self.regular_user = UserFactory.create()
        self.anonymous_user = AnonymousUser()
        self.project = ProjectFactory(add_admins=[self.admin])
        self.sapelli_project = SapelliProjectFactory.create(
            **{'geokey_project': self.project})
        self.file = get_log_file()

    def tearDown(self):
        """Tear down test."""
        for sapelli_log_file in SapelliLogFile.objects.all():
            sapelli_log_file.delete()

    def post(self, user, data=None):
        """Custom method for testing POST."""
        if data is None:
            data = {'file': self.file}

        url = reverse(
            'geokey_sapelli:project_logs_api_via_personal_info',
            kwargs={
                'sapelli_project_id': self.sapelli_project.sapelli_id,
                'sapelli_project_fingerprint': self.sapelli_project.sapelli_fingerprint,
            })

        request = self.factory.post(url, data)
        force_authenticate(request, user)
        view = SapelliLogsViaPersonalInfo.as_view()
        return view(
            request,
            sapelli_project_id=self.sapelli_project.sapelli_id,
            sapelli_project_fingerprint=self.sapelli_project.sapelli_fingerprint,
        ).render()

    def test_post_with_admin(self):
        """Test POST with admin."""
        response = self.post(self.admin)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_with_regular_user(self):
        """Test POST with regular user."""
        response = self.post(self.regular_user)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_with_anonymous(self):
        """Test POST with anonymous user."""
        response = self.post(self.anonymous_user)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_when_assigning_name(self):
        """Test POST when assigning name."""
        data = {'name': 'Test Name', 'file': self.file}
        response = self.post(self.admin, data)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            'Test Name')
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)


class SapelliLogsViaGeoKeyInfoTest(TestCase):
    """Test public API for Sapelli logs via the Sapelli info."""

    def setUp(self):
        """Set up test."""
        self.factory = APIRequestFactory()
        self.admin = UserFactory.create()
        self.regular_user = UserFactory.create()
        self.anonymous_user = AnonymousUser()
        self.project = ProjectFactory(add_admins=[self.admin])
        self.sapelli_project = SapelliProjectFactory.create(
            **{'geokey_project': self.project})
        self.file = get_log_file()

    def tearDown(self):
        """Tear down test."""
        for sapelli_log_file in SapelliLogFile.objects.all():
            sapelli_log_file.delete()

    def post(self, user, data=None):
        """Custom method for testing POST."""
        if data is None:
            data = {'file': self.file}

        url = reverse(
            'geokey_sapelli:project_logs_api_via_gk_info',
            kwargs={'project_id': self.project.id})

        request = self.factory.post(url, data)
        force_authenticate(request, user)
        view = SapelliLogsViaGeoKeyInfo.as_view()
        return view(
            request,
            project_id=self.project.id,
        ).render()

    def test_post_with_admin(self):
        """Test POST with admin."""
        response = self.post(self.admin)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_with_regular_user(self):
        """Test POST with regular user."""
        response = self.post(self.regular_user)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_with_anonymous(self):
        """Test POST with anonymous user."""
        response = self.post(self.anonymous_user)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            self.file_name)
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)

    def test_post_when_assigning_name(self):
        """Test POST when assigning name."""
        data = {'name': 'Test Name', 'file': self.file}
        response = self.post(self.admin, data)
        self.assertEqual(response.status_code, 201)
        reference = SapelliLogFile.objects.latest('pk')
        self.assertEqual(
            reference.name,
            'Test Name')
        self.assertEqual(
            reference.created_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertNotEqual(
            reference.uploaded_at,
            datetime(2015, 01, 20, 18, 02, 12).replace(tzinfo=utc))
        self.assertEqual(
            reference.sapelli_project,
            self.sapelli_project)
