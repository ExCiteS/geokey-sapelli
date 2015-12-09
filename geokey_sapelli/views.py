from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.conf import settings

from braces.views import LoginRequiredMixin

from rest_framework.views import APIView
from rest_framework.response import Response

from oauth2_provider.views.base import TokenView

from geokey.core.decorators import (
    handle_exceptions_for_ajax,
    handle_exceptions_for_admin
)
from geokey.projects.models import Project

from .models import SapelliProject
from helper.sapelli_loader import SapelliLoaderMixin
from helper.sapelli_exceptions import SapelliException, SapelliSAPException, SapelliXMLException, SapelliDuplicateException

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
        projects = SapelliProject.objects.get_list_for_contribution(self.request.user)
        context = {'projects': projects}
        return self.add_menu(context)


class ProjectUpload(AbstractSapelliView, SapelliLoaderMixin):
    """
    Presents a form to upload a .sap file to create a new project.
    """
    template_name = 'sapelli_upload_project.html'

    @staticmethod
    def get_menu_label():
        return 'Upload new Sapelli project'

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
            sapelli_project = self.load(request.FILES.get('project'), request.user)

            messages.success(self.request, "The project has been created.")

            return redirect(
                'geokey_sapelli:data_csv_upload',
                project_id=sapelli_project.project.id
            )
        except SapelliSAPException, e:
            messages.error(
                self.request,
                'The uploaded file is not a valid Sapelli project file (*.sap) [' + str(e) + ']'
            )
        except SapelliXMLException, e:
            messages.error(
                self.request,
                'Failed to parse PROJECT.xml file [' + str(e) + ']'
            )
        except SapelliDuplicateException:
            messages.error(
                self.request,
                'You already have a matching Sapelli project.'
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
            Identifies the project on the data base

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
            Identifies the project on the data base

        Returns
        -------
        django.http.HttpResponse
            The rendered view
        """
        context = self.get_context_data(project_id)
        sapelli_project = context.get('sapelli_project')

        if sapelli_project is not None:
            the_file = request.FILES.get('data')
            form_id = request.POST.get('form_id')
            # TODO read Sapelli Form id (String!) from the csv file header and get corresponding SapelliForm that way!

            imported, updated, ignored = sapelli_project.import_from_csv(request.user, form_id, the_file)

            messages.success(
                self.request,
                "%s records have been added to the project. %s have been "
                "updated. %s have been ignored because they were identical "
                "to existing contributions." % (imported, updated, ignored)
            )

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


class ProjectUploadAPI(APIView, SapelliLoaderMixin):
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
            sapelli_project = self.load(request.FILES.get('project'), request.user)
        except SapelliException, e:
            return Response({'error': str(e)})
        else:
            # return project description (as json) to signal successful upload:
            Response(sapelli_project.get_description())


class DataCSVUploadAPI(APIView):
    """
    API Endpoint for uploading data as CSV.
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
        project_id : int
            Identifies the GeoKey project on the data base
        category_id : int
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
            #try:
            the_file = request.FILES.get('data')
            imported, updated, ignored = sapelli_project.import_from_csv(request.user, category_id, the_file)
            return Response({'added': imported, 'updated': updated, 'duplicates': ignored})
            #except Exception, e:
            #    return Response({'error': str(e)})


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
            project = Project.objects.get(pk=project_id)
            observation = project.observations.get(category_id=category_id, properties__at_StartTime=sapelli_record_start_time, properties__at_DeviceId=sapelli_record_device_id)
        except Project.DoesNotExist:
            return Response({'error': 'No such project (id: %s)' % project_id}, status=404)
        #except Exception, e:
        #        return Response({'error': str(e)})
        return Response({'observation_id': observation.id})
