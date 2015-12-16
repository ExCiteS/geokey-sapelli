import os
import qrcode

from StringIO import StringIO

from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.http import HttpResponse

from braces.views import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response

from oauth2_provider.views.base import TokenView
from oauth2_provider.models import AccessToken

from geokey.core.decorators import (
    handle_exceptions_for_ajax,
    handle_exceptions_for_admin
)
from geokey.projects.models import Project

from . import __version__

from .models import SapelliProject
from .helper.sapelli_loader import load_from_sap
from .helper.sapelli_exceptions import (
    SapelliException,
    SapelliSAPException,
    SapelliXMLException,
    SapelliDuplicateException,
    SapelliCSVException
)


from helper.dynamic_menu import MenuEntry


# ############################################################################
#
# Views
#
# ############################################################################

class AbstractSapelliView(LoginRequiredMixin, TemplateView):
    @staticmethod
    def get_menu_label():
        return None

    @staticmethod
    def get_menu_url():
        return None

    def add_menu(self, context):
        menu_entries = []
        for subclass in AbstractSapelliView.__subclasses__():
            if subclass.get_menu_label() and subclass.get_menu_url():
                menu_entries.append(MenuEntry(label=subclass.get_menu_label(), url=subclass.get_menu_url(), active=(self.__class__ == subclass)))

        context['menu_entries'] = menu_entries
        context['GEOKEY_SAPELLI_VERSION'] = __version__
        return context


class ProjectList(AbstractSapelliView):
    """
    Presents a list of all projects the user can access. Is also the starting
    page for the Sapelli extension.
    """
    template_name = 'sapelli_project_list.html'

    @staticmethod
    def get_menu_label():
        return 'Project list'

    @staticmethod
    def get_menu_url():
        return 'geokey_sapelli:index'

    def get_context_data(self):
        """
        Returns the context to render the view. Contains a list of Sapelli
        projects that are available for the user to contribute to.

        Returns
        -------
        dict
        """
        context = {'sapelli_projects': SapelliProject.objects.get_list_for_contribution(self.request.user)}
        return self.add_menu(context)


class ProjectUpload(AbstractSapelliView):
    """
    Presents a form to upload a .sap file to create a new project.
    """
    template_name = 'sapelli_upload_project.html'

    @staticmethod
    def get_menu_label():
        return 'Add project'

    @staticmethod
    def get_menu_url():
        return 'geokey_sapelli:project_upload'

    def get_context_data(self):
        return self.add_menu({})

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
            messages.warning(
                self.request,
                'You already have access to a matching Sapelli project.'
            )
        except SapelliException, e:
            messages.warning(
                self.request,
                'Sapelli extension configuration problem:\n\n' + str(e)
            )
        return self.render_to_response({})


class DataCSVUpload(AbstractSapelliView):
    """
    Presents a form to upload CSV files to create contributions.
    """
    template_name = 'sapelli_upload_data_csv.html'

    @handle_exceptions_for_admin
    def get_context_data(self, project_id):
        """
        Returns the context to render the view. Contains a Sapelli project.

        Parameter
        ---------
        project_id : int
            Identifies the GeoKey project on the data base

        Returns
        -------
        dict
        """
        project = SapelliProject.objects.get_single_for_contribution(self.request.user, project_id)
        context = {'sapelli_project': project}
        return self.add_menu(context)

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
                imported, updated, ignored_duplicate, ignored_no_loc = sapelli_project.import_from_csv(request.user, csv_file, form_category_id)
                messages.success(
                    self.request,
                    "Result:\n"
                    " - %s records have been added as project contributions;\n"
                    " - %s have been updated;\n"
                    " - %s have been ignored because they were identical to existing contributions;\n"
                    " - %s where ignored because they lack location coordinates."
                    % (imported, updated, ignored_duplicate, ignored_no_loc)
                )
            except SapelliCSVException, e:
                messages.error(self.request, 'Failed to process CSV file, due to:\n\n' + str(e))

        return self.render_to_response(context)


# ############################################################################
#
# Public API views
#
# ############################################################################

class LoginAPI(TokenView):
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
            Object representing the request,
            expected to contain POST fields 'username' and 'password'.

        Returns
        -------
        If username and password are correct/authorised, the response is a JSON
        object containing the OAuth access_token, if not the response is a JSON
        object containing error information.

        Raises
        ------
        TODO
        """
        # ensure POST request is mutable:
        # (this isn't always the case, see http://stackoverflow.com/q/12611345)
        if not (request.POST._mutable):
            request.POST = request.POST.copy()
        request.POST['client_id'] = settings.SAPELLI_CLIENT_ID
        request.POST['grant_type'] = 'password'

        return super(LoginAPI, self).post(request, *args, **kwargs)


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
        JSON with information about the GeoKey project and its categories (corresponding to Sapelli Forms).

        Raises
        ------
        TODO
        """
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution_by_sapelli_info(request.user, sapelli_project_id, sapelli_project_fingerprint)
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
    api/sapelli/projects/xxxx/csv_upload/yyyy/
    """
    @handle_exceptions_for_ajax
    def post(self, request, project_id, category_id):
        """
        TODO

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        project_id : str
            Identifies the GeoKey project on the data base
        category_id : str
            Identifies the GeoKey category and thereby the SapelliForm
        
        Returns
        -------
        TODO

        Raises
        ------
        TODO
        """
        # TODO read Sapelli Form id (String!) from the csv file header and get corresponding SapelliForm that way!
        
        if request.user.is_anonymous():
            raise PermissionDenied('API access not authorised, please login.')
        try:
            sapelli_project = SapelliProject.objects.get_single_for_contribution(self.request.user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        else:
            try:
                csv_file = request.FILES.get('csv_file')
                imported, updated, ignored_duplicate, ignored_no_loc = sapelli_project.import_from_csv(request.user, csv_file, category_id)
                return Response({'added': imported, 'updated': updated, 'ignored_duplicates': ignored_duplicate, 'ignored_no_loc': ignored_no_loc})
            except BaseException, e:
                return Response({'error': str(e)})


class FindObservationAPI(APIView):
    """
    TODO
    """
    @handle_exceptions_for_ajax
    def get(self, request, project_id, category_id, sapelli_record_start_time, sapelli_record_device_id):
        """
        TODO

        Parameter
        ---------
        request : rest_framework.request.Request
            Object representing the request.
        project_id : int
            Identifies the GeoKey project on the data base
        category_id : int
            Identifies the category on the data base
        sapelli_record_start_time : string
            ISO 8601 timestamp with ms accuracy and UTC offset
        sapelli_record_device_id : int
            Sapelli-generated device id

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
            geokey_project = Project.objects.get(pk=project_id)
            observation = geokey_project.observations.get(
                category_id=category_id,
                properties__at_StartTime=sapelli_record_start_time,
                properties__at_DeviceId=sapelli_record_device_id)
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
        #else:
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
            SapelliProject.objects.get_single_for_contribution(self.request.user, project_id)
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        try:
            # Generate download url:
            sap_download_url = (
                request.build_absolute_uri(reverse('geokey_sapelli:sap_download_api', kwargs={'project_id': project_id})) +
                '?access_token=' + AccessToken.objects.filter(user=request.user)[0].token)
            # generate QR png image:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=5,
                border=0,
                )
            qr.add_data(sap_download_url)
            qr.make(fit=True)
            img_buffer = StringIO()
            qr.make_image().save(img_buffer, "PNG")
            # Grab img file from in-memory, make response with correct MIME-type
            response = HttpResponse(img_buffer.getvalue(), content_type = 'image/png')
            # ..and correct content-disposition
            response['Content-Disposition'] = 'attachment; filename=%s' % request.path[request.path.rfind('/')+1:]
            return response
        except BaseException, e:
            return Response({'error': str(e)})
