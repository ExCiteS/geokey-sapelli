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
        raise NotImplementedError

    @staticmethod
    def get_menu_url():
        raise NotImplementedError

    def add_menu(self, context):
        context['menu_entries'] = [MenuEntry(label=subclass.get_menu_label(), url=subclass.get_menu_url(), active=(self.__class__ == subclass)) for subclass in AbstractSapelliView.__subclasses__()]
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
        projects that are available for the user.

        Returns
        -------
        dict
        """
        projects = SapelliProject.objects.get_list(self.request.user)
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
                'geokey_sapelli:data_upload',
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


class DataUpload(LoginRequiredMixin, TemplateView):
    """
    Presents a form to upload CSV files to create contributions.
    """
    template_name = 'sapelli_upload_data.html'

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
        project = SapelliProject.objects.get_single(
            self.request.user, project_id)
        return {'sapelli_project': project}

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
        project = context.get('sapelli_project')

        if project is not None:
            file = request.FILES.get('data')
            form_id = request.POST.get('form_id')

            num_records = project.import_from_csv(request.user, form_id, file)

            messages.success(
                self.request,
                "%s records have been added to the project" % num_records
            )

        return self.render_to_response(context)


# ############################################################################
#
# Public API views
#
# ############################################################################

class LoginAPI(TokenView):
    def post(self, request, *args, **kwargs):
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
            sapelli_project = SapelliProject.objects.get_single_by_sapelli_info(request.user, sapelli_project_id, sapelli_project_fingerprint)
        # TODO no access exception
        except SapelliProject.DoesNotExist:
            return Response({'error': 'No such project'})
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
