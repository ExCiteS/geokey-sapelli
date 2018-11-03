# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import qrcode

from StringIO import StringIO
from zipfile import ZipFile
from dateutil import parser

from django.views.generic import View, TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone, dateformat

from braces.views import LoginRequiredMixin
from wsgiref.util import FileWrapper

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from oauth2_provider.models import AccessToken
from oauth2_provider.views.base import TokenView

from geokey.users.models import User
from geokey.core.decorators import (
    handle_exceptions_for_ajax,
    handle_exceptions_for_admin
)
from geokey.projects.models import Project

from .models import SapelliProject, SAPDownloadQRLink, SapelliLogFile
from .helper.sapelli_loader import load_from_sap
from .helper.sapelli_exceptions import (
    SapelliException,
    SapelliSAPException,
    SapelliXMLException,
    SapelliDuplicateException,
    SapelliCSVException
)
from .helper.install_checks import check_extension

from geokey_sapelli.serializers import SapelliLogFileSerializer


# ############################################################################
#
# Views
#
# ############################################################################

class AbstractSapelliView(LoginRequiredMixin, TemplateView):

    def check(self):
        """Check if extension is correctly installed."""
        try:
            check_extension()
        except SapelliException, se:
            messages.error(
                self.request,
                'The Sapelli extension is not properly installed: ' + str(se))


class ProjectList(AbstractSapelliView):
    """
    Presents a list of all projects the user can access. Is also the starting
    page for the Sapelli extension.
    """
    template_name = 'sapelli/index.html'

    def get_context_data(self):
        """
        Returns the context to render the view. Contains a list of Sapelli
        projects that are available for the user to contribute to.

        Returns
        -------
        dict
        """
        context = {'sapelli_projects': SapelliProject.objects.get_list_for_contribution(self.request.user)}
        self.check()
        return context


class ProjectUpload(AbstractSapelliView):
    """
    Presents a form to upload a .sap file to create a new project.
    """
    template_name = 'sapelli/upload_sapelli_project.html'

    def post(self, request):
        """
        Handles the POST request.

        Parameter
        ---------
        django.http.HttpRequest
            Object representing the request.

        Returns
        -------
        django.http.HttpResponseRedirect
            Redirecting to the data upload form
        """
        try:
            sapelli_project = load_from_sap(request.FILES.get('sap_file'), request.user)

            messages.success(self.request, 'The project has been created.')
            return redirect(
                'geokey_sapelli:data_csv_upload',
                project_id=sapelli_project.geokey_project.id
            )
        except SapelliSAPException, e:
            messages.error(
                self.request,
                'Failed to load Sapelli project, due to:\n\n' + str(e)
            )
            if not (e.java_stacktrace is None):
                messages.error(
                    self.request,
                    e.java_stacktrace,
                    extra_tags='java_stacktrace'
                )
        except SapelliXMLException, e:
            messages.error(
                self.request,
                'Failed to parse PROJECT.xml file, due to:\n\n' + str(e)
            )
        except SapelliDuplicateException:
            messages.error(
                self.request,
                'This Sapelli project has already been uploaded by you or '
                'someone else on the platform. Please make sure you\'re '
                'allowed to access and contribute to it, otherwise try to '
                'change the Sapelli project ID.'
            )
        except SapelliException, e:
            messages.warning(
                self.request,
                'Sapelli extension configuration problem:\n\n' + str(e)
            )
        return self.render_to_response({})


class SapelliProjectMixin(LoginRequiredMixin):
    """Sapelli project mixin (requires a user to be logged in)."""

    def get_object(self, user, sapelli_project_id):
        """
        Get the object.

        Parameters
        ----------
        sapelli_project_id : int
            Identifies the Sapelli project in the database.

        Returns
        -------
        geokey_sapelli.models.SapelliProject
            Object found by ID, only if user is administrator.
        """
        return SapelliProject.objects.get_single_for_administration(
            user,
            sapelli_project_id)

    def get_logs(self, sapelli_project, date_from, date_to):
        """Get all logs."""
        logs = SapelliLogFile.objects.filter(sapelli_project=sapelli_project)

        if date_from:
            try:
                date_from = parser.parse(date_from)
            except ValueError:
                messages.error(self.request, 'Invalid `from` date.')
                date_from = None
        if date_to:
            try:
                date_to = parser.parse(date_to)
            except ValueError:
                messages.error(self.request, 'Invalid `to` date.')
                date_to = None

        if date_from and date_to and date_to < date_from:
            messages.error(self.request, 'Invalid date range.')
        else:
            if date_from:
                logs = logs.filter(created_at__gte=date_from)
            if date_to:
                logs = logs.filter(created_at__lt=date_to)

        return logs

    def paginate_logs(self, logs, page):
        """Paginate all logs."""
        paginator = Paginator(logs.order_by('-created_at'), 50)

        try:
            logs = paginator.page(page)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)

        return logs

    def get_context_data(self, sapelli_project_id, *args, **kwargs):
        """
        Return the context to render the view.

        Parameters
        ----------
        sapelli_project_id : int
            Identifies the Sapelli project in the database.

        Returns
        -------
        dict
            Context with Sapelli project or an error message.
        """
        user = self.request.user

        try:
            return {
                'sapelli_project': self.get_object(user, sapelli_project_id),
            }
        except SapelliProject.DoesNotExist:
            return {
                'error': 'Not found',
                'error_description': 'Sapelli project not found.',
            }


class SapelliProjectAbstractView(AbstractSapelliView):
    """Abstract view for Sapelli project."""

    @handle_exceptions_for_admin
    def get_context_data(self, project_id):
        """
        Return the context to render the view. Contains Sapelli project.

        Parameters
        ----------
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        dict
        """
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(
                self.request.user,
                project_id)
            return {'sapelli_project': sapelli_project}
        except SapelliProject.DoesNotExist:
            return {
                'error_description': 'Sapelli project not found.',
                'error': 'Not found'
            }


class DataCSVUpload(SapelliProjectAbstractView):
    """
    Presents a form to upload CSV files to create contributions.
    """
    template_name = 'sapelli/upload_data_csv.html'

    def post(self, request, project_id):
        """
        Uploads the CSV and creates the contributions.

        Parameter
        ---------
        django.http.HttpRequest
            Object representing the request.
        project_id : int
            Identifies the Geokey project on the data base

        Returns
        -------
        django.http.HttpResponse
            The rendered view
        """
        context = self.get_context_data(project_id)
        sapelli_project = context.get('sapelli_project')

        if sapelli_project is not None:
            csv_file = request.FILES.get('csv_file')
            form_category_id = request.POST.get('form_category_id')
            try:
                imported, imported_joined_locations, imported_no_location, updated, ignored_duplicate = sapelli_project.import_from_csv(request.user, csv_file, form_category_id)
                messages.success(
                    self.request,
                    "Result:\n"
                    " - %s records have been added as project contributions;\n"
                    " - %s records have been added as project contributions with joined locations;\n"
                    " - %s records have been added as project contributions without locations;\n"
                    " - %s have been updated;\n"
                    " - %s have been ignored because they were identical to existing contributions;"
                    % (imported, imported_joined_locations, imported_no_location, updated, ignored_duplicate)
                )
            except SapelliCSVException, e:
                messages.error(self.request, 'Failed to process CSV file, due to:\n\n' + str(e))

        return self.render_to_response(context)


class DataLogsDownload(SapelliProjectMixin, TemplateView):
    """Admin page for all Sapelli logs."""

    template_name = 'sapelli/logs.html'

    def get_context_data(self, project_id, *args, **kwargs):
        """
        Return the context to render the view.

        Parameters
        ----------
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        dict
            Context with Sapelli project, filtered and paged logs.
        """
        context = super(DataLogsDownload, self).get_context_data(
            project_id,
            *args,
            **kwargs)

        sapelli_project = context.get('sapelli_project')
        if sapelli_project:
            data = self.request.GET
            date_from = kwargs.get('date_from') or data.get('date_from')
            date_to = kwargs.get('date_to') or data.get('date_to')

            logs = self.get_logs(
                sapelli_project,
                date_from,
                date_to)

            context['date_from'] = date_from
            context['date_to'] = date_to
            context['logs'] = self.paginate_logs(
                logs,
                self.request.GET.get('page'))

        return context

    def post(self, request, project_id, *args, **kwargs):
        """
        Handle POST request.

        Parameters
        ----------
        request : django.http.HttpRequest
            Object representing the request.
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        django.http.HttpResponse
            Rendered template.
        """
        context = self.get_context_data(
            project_id,
            date_from=request.POST.get('date-from'),
            date_to=request.POST.get('date-to'))

        return self.render_to_response(context)


class LogsZipView(SapelliProjectMixin, View):
    """Admin page for downloading all Sapelli logs as ZIP archive."""

    def get(self, request, project_id, file, *args, **kwargs):
        """
        Handle GET request.

        Parameters
        ----------
        request : django.http.HttpRequest
            Object representing the request.
        project_id : int
            Identifies the GeoKey project in the database.
        file : str
            Identifies the file name.

        Returns
        -------
        django.http.HttpResponseRedirect
            When nothing to archive.
        """
        context = self.get_context_data(
            project_id,
            *args,
            **kwargs)

        sapelli_project = context.get('sapelli_project')
        if sapelli_project:
            data = self.request.GET

            logs = self.get_logs(
                sapelli_project,
                data.get('date_from'),
                data.get('date_to'))

            if len(logs) == 0:
                messages.error(self.request, 'Nothing to archive.')
            else:
                temp_file = StringIO()
                with ZipFile(temp_file, 'w') as archive:
                    for log in logs:
                        archive.write(log.file.path, log.name)

                response = HttpResponse(
                    temp_file.getvalue(),
                    content_type='application/x-zip-compressed')
                response['Content-Disposition'] = 'attachment; filename="%s - %s.zip"' % (
                    file,
                    dateformat.format(timezone.now(), 'l, jS \\o\\f F, Y'))

                return response

        return redirect('geokey_sapelli:logs', project_id=project_id)


# ############################################################################
#
# Public API views
#
# ############################################################################

class LoginAPI(TokenView, APIView):
    """
    This API allows Sapelli Collector instances (running on smartphones) to
    login to the GeoKey server without the need for full OAuth-style
    authentication. Instead all that is needed is a POST request which
    supplies username and password.
    The reason is that the Sapelli Collector app has to work with _any_ GeoKey
    server instance, meaning that we cannot simply hardcode a predefined OAuth
    client-id in the app source code, as it would be different on different
    GeoKey servers. Instead we let the geokey-sapelli extension play the role
    of the application/client (registered to the GeoKey server, as explained in
    README.rst) and let the smartphone app authenticate users through this API.
    """
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for user authentication.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request, expected to contain POST fields 'username'
            (with the user's email address!) and 'password'.

        Returns
        -------
        If username (which is actually an email address) and password are
        correct/authorised, the response is a JSON object containing the OAuth
        access_token (+ 'expires_at' timestamp), if not the response is a JSON object
        containing error information.
        """
        try:
            # Create new POST HttpRequest (the request we got is a rest_framework.request.Request) and copy the POST parameters:
            httpRequest = HttpRequest()
            httpRequest.method = 'POST'
            httpRequest.POST = request.POST.copy()

            # Keep for backwards compatibility
            httpRequest.POST['grant_type'] = httpRequest.POST.get('grant_type', 'password')

            # Add client_id parameter:
            try:
                httpRequest.POST['client_id'] = settings.SAPELLI_CLIENT_ID
            except AttributeError, e:
                raise SapelliException(
                    'geokey-sapelli is not properly configured as an application on the server: ' + str(e))

            # Use super class to perform actual login:
            response = super(LoginAPI, self).post(httpRequest, *args, **kwargs)

            # Check response:
            if response.status_code != 200:
                # return response as-is:
                return response
            try:
                # add expires time:
                response_json = json.loads(response.content)
                access_token = AccessToken.objects.get(token=response_json.get('access_token'))
                response_json['expires_at'] = access_token.expires.isoformat()
                return Response(response_json)
            except BaseException, e:
                # return response as-is:
                return response
        except BaseException, e:
            return Response({'error': str(e)})

    def get(self, request):
        """
        Handles GET requests which are used to checked if the user is (still) logged in
        (i.e. if the access_token he/she has is still valid).

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.

        Returns
        -------
        JSON object with boolean 'logged_in' value indicating
        whether the user is logged in or not.
        """
        return Response({'logged_in': (not request.user.is_anonymous())})


class ProjectDescriptionAPI(APIView):
    """
    API Endpoint for consulting the mapping of Sapelli projects
    (identified by id and fingerprint) to corresponding GeoKey projects
    api/sapelli/projects/description/xxxx/yyyyyyy
    With xxxx = Sapelli Project ID; and yyyyyyy = Sapelli Project Fingerprint
    """
    @handle_exceptions_for_ajax
    def get(self, request, sapelli_project_id, sapelli_project_fingerprint):
        """
        Handles GET requests for information about the GeoKey project that
        corresponds to the Sapelli project with the given id and fingerprint.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        sapelli_project_id : string
            Sapelli Project ID
        sapelli_project_fingerprint : string
            Sapelli Project Fingerprint

        Returns
        -------
        JSON with information about the GeoKey project and its categories (corresponding to Sapelli Forms),
        or one of these error messages: 'User cannot contribute to project', 'No such project'.
        """
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution_by_sapelli_info(request.user, sapelli_project_id, sapelli_project_fingerprint)
            # may throw PermissionDenied, which is handled by the @handle_exceptions_for_ajax decorator
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project'}, status=404)
        else:
            # return project description (as json):
            return Response(sapelli_project.get_description())


class ProjectUploadAPI(APIView):
    """
    API Endpoint for uploading a new Sapelli project.
    api/sapelli/projects/new/
    """
    @handle_exceptions_for_ajax
    def post(self, request):
        """
        TODO

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        TODO

        Returns
        -------
        TODO

        Raises
        ------
        TODO
        """
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        try:
            sapelli_project = load_from_sap(request.FILES.get('sap_file'), request.user)
        except SapelliSAPException, e:
            error_response = {'error': str(e)}
            if e.java_stacktrace is not None:
                error_response['java_stacktrace'] = e.java_stacktrace
            return Response(error_response)
        except SapelliException, e:
            return Response({'error': str(e)})
        else:
            # return project description (as json) to signal successful upload:
            Response(sapelli_project.get_description())



class DataCSVUploadAPI(APIView):
    """
    API Endpoint for uploading Sapelli records as CSV.
    api/sapelli/projects/pppp/csv_upload/
    """
    @handle_exceptions_for_ajax
    def post(self, request, project_id):
        """
        POST request handler to deal with uploaded CSV file.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
            Expected to contain a file identified as 'csv_file'. The CSV file
            is expected to conform to the files are generated by Sapelli's
            CSVRecordsExporter class (https://github.com/ExCiteS/Sapelli/blob/master/Library/src/uk/ac/ucl/excites/sapelli/storage/eximport/csv/CSVRecordsExporter.java).
            With a comma as separator and with the full header containing model/schema identification.

        project_id : str
            Identifies the GeoKey project on the data base

        Returns
        -------
        JSON with feedback about record import (i.e. number of 'added', 'updated', 'ignored_duplicates' and 'ignored_no_loc' records),
        or an 'error' message.
        """
        user = request.user
        if user.is_anonymous():
            user = User.objects.get(display_name='AnonymousUser')
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        else:
            try:
                csv_file = request.FILES.get('csv_file')
                imported, imported_joined_locations, imported_no_location, updated, ignored_duplicate = sapelli_project.import_from_csv(user, csv_file)
                return Response({'added': imported, 'added_joined_locs': imported_joined_locations, 'added_no_loc': imported_no_location, 'updated': updated, 'ignored_duplicates': ignored_duplicate, 'ignored_no_loc': ignored_no_loc})
            except BaseException, e:
                return Response({'error': str(e)})


class FindObservationAPI(APIView):
    """
    API Endpoint for requesting the observation_id of a Sapelli record that is
    assumed to exist on the server.
    api/sapelli/projects/pppp/find_observation/cccc/ssss/dddd/
    """
    @handle_exceptions_for_ajax
    def post(self, request, project_id, category_id):
        """
        POST request handler to look-up the Observation matching the given parameters.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request, expected to contain POST parameters
            'sap_rec_StartTime' (the "StartTime" of the Sapelli record, formatted as an
            ISO 8601 timestamp with ms accuracy and UTC offset) and 'sap_rec_DeviceID'
            (a Sapelli-generated device id, unsigned 32 bit integer, encoded as a string).
        project_id : int
            Identifies the GeoKey project on the data base
        category_id : int
            Identifies the category on the data base

        Returns
        -------
        the id of the Observation or an error.
        """
        sap_rec_start_time = request.POST.get('sap_rec_StartTime')
        sap_rec_device_id = request.POST.get('sap_rec_DeviceID')
        if sap_rec_start_time is None or sap_rec_device_id is None:
            return Response({'error': 'sap_rec_StartTime or sap_rec_DeviceID parameter missing'})
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(request.user, project_id)
            observation = sapelli_project.geokey_project.observations.get(
                category_id=category_id,
                properties__StartTime=sap_rec_start_time,
                properties__DeviceId=sap_rec_device_id)
        except Project.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        except BaseException, e:
            return Response({'error': str(e)})
        return Response({'observation_id': observation.id})


class SAPDownloadAPI(APIView):
    @handle_exceptions_for_ajax
    def get(self, request, project_id):
        """
        API end-point which allows the SAP file of a project to be downloaded.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        project_id : str
            Identifies the GeoKey project on the data base

        Returns
        -------
        SAP/ZIP file download
        """
        # Check user access:
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        # Check project access:
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(self.request.user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        # Check if we have a sap_path and whether the file is actually there:
        if sapelli_project.sap_path is None or not os.path.isfile(sapelli_project.sap_path):
            return Response({'error': 'No SAP file available for download'}, status=404)
        # else:
        wrapper = FileWrapper(file(sapelli_project.sap_path))
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(sapelli_project.sap_path)
        response['Content-Length'] = os.path.getsize(sapelli_project.sap_path)
        return response


class SAPDownloadQRLinkAPI(APIView):
    @handle_exceptions_for_ajax
    def get(self, request, project_id):
        """
        API end-point which produces PNG images that contain a QR code
        which encodes a link to download the SAP file of a project.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        project_id : str
            Identifies the GeoKey project on the data base

        Returns
        -------
        PNG image download
        """
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        # Check if current user can contribute to the project:
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(request.user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        try:
            qr_link = None
            try:  # Try getting previously generated link/token:
                qr_link = SAPDownloadQRLink.objects.filter(access_token__user=request.user, sapelli_project=sapelli_project).latest('access_token__expires')
            except BaseException, e:
                pass
            if qr_link is None or qr_link.access_token.is_expired():
                if (qr_link is not None):
                    qr_link.access_token.delete()  # qr_link will be deleted as well
                # Generate new access token (valid for 1 day):
                qr_link = SAPDownloadQRLink.create(user=request.user, sapelli_project=sapelli_project, days_valid=1)
            # Generate download url:
            sap_download_url = (
                request.build_absolute_uri(reverse('geokey_sapelli:sap_download_api', kwargs={'project_id': project_id})) +
                '?access_token=' + qr_link.access_token.token)
            # Generate QR code PNG image:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=5,
                border=0)
            qr.add_data(sap_download_url)
            qr.make(fit=True)
            img_buffer = StringIO()
            qr.make_image().save(img_buffer, "PNG")
            # Grab img file from in-memory, make response with correct MIME-type
            response = HttpResponse(img_buffer.getvalue(), content_type='image/png')
            # ..and correct content-disposition
            response['Content-Disposition'] = 'attachment; filename=%s' % request.path[request.path.rfind('/') + 1:]
            # Add additional info as response headers:
            response['X-QR-URL'] = sap_download_url
            response['X-QR-Access-Token'] = qr_link.access_token.token
            response['X-QR-Access-Token-Expires'] = qr_link.access_token.expires.isoformat()
            return response
        except BaseException, e:
            return Response({'error': str(e)})

    @handle_exceptions_for_ajax
    def delete(self, request, project_id):
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        # Check if current user can contribute to the project:
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(request.user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        try:  # Try getting & deleting previously generated link/token:
            qr_link = SAPDownloadQRLink.objects.filter(access_token__user=request.user, sapelli_project=sapelli_project).latest('access_token__expires')
            qr_link.access_token.delete()  # qr_link will be deleted as well
        except BaseException, e:
            return Response({'error': str(e)})
        return Response({'deleted': True})


class SapelliLogsAbstractAPIView(APIView):
    """Abstract API for Sapelli logs."""

    def get_user(self, request):
        """
        Get user of a request.

        Parameters
        ----------
        request : rest_framework.request.Request
            Object representing the request.

        Returns
        -------
        geokey.users.models.User
            User of a request.
        """
        user = request.user

        if user.is_anonymous():
            user = User.objects.get(display_name='AnonymousUser')

        return user

    def create_and_respond(self, request, sapelli_project):
        """
        Respond to a POST request by creating a log file.

        Parameters
        ----------
        request : rest_framework.request.Request
            Object representing the request.
        sapelli_project : geokey_sapelli.models.SapelliProject
            Sapelli project the log file should be added to.

        Returns
        -------
        rest_framework.response.Respone
            Contains the serialized log file.

        Raises
        ------
        MalformedRequestData
            When name is not set or file is not attached.
        PermissionDenied
            When user is not allowed to contribute to the project.
        """
        user = self.get_user(request)

        name = self.request.POST.get('name')
        file = self.request.FILES.get('file')

        if file is None:
            return Response({'error': 'No file attached.'}, status=406)

        log_file = SapelliLogFile.create(
            name=name,
            creator=user,
            sapelli_project=sapelli_project,
            file=file)

        serializer = SapelliLogFileSerializer(log_file, context={'user': user})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SapelliLogsViaPersonalInfo(SapelliLogsAbstractAPIView):
    """Public API for Sapelli logs via the personal (GeoKey) info."""

    def post(self, request, sapelli_project_id, sapelli_project_fingerprint):
        """
        Handle POST request.

        Add a new log file to the Sapelli project.

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        sapelli_project_id : string
            Identifies the Sapelli project ID in the database.
        sapelli_project_fingerprint : string
            Identifies the Sapelli project fingerprint in the database.

        Returns
        -------
        rest_framework.response.Respone
            Contains the serialised log file.
        """
        try:
            sapelli_project = SapelliProject.objects.get(
                sapelli_id=sapelli_project_id,
                sapelli_fingerprint=sapelli_project_fingerprint)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project.'}, status=404)

        return self.create_and_respond(request, sapelli_project)


class SapelliLogsViaGeoKeyInfo(SapelliLogsAbstractAPIView):
    """Public API for Sapelli logs via the Sapelli info."""

    def post(self, request, project_id):
        """
        Handle POST request.

        Add a new log file to the Sapelli project.

        Parameters
        ----------
        request : rest_framework.request.Request
            Object representing the request.
        project_id : int
            Identifies the GeoKey project in the database.

        Returns
        -------
        rest_framework.response.Respone
            Contains the serialised log file.
        """
        try:
            sapelli_project = SapelliProject.objects.get(
                geokey_project__id=project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project.'}, status=404)

        return self.create_and_respond(request, sapelli_project)
