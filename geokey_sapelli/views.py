from zipfile import BadZipfile

from django.views.generic import TemplateView
from django.contrib import messages
from django.shortcuts import redirect
from braces.views import LoginRequiredMixin

from geokey.core.decorators import handle_exceptions_for_admin

from .models import SapelliProject
from helper.xml_parsers import parse_decision_tree, extract_sapelli
from helper.project_mapper import create_project

from helper.dynamic_menu import MenuEntry

class AbstractSapelliView(LoginRequiredMixin, TemplateView):
    @staticmethod
    def get_menu_label():
        raise NotImplementedError
    
    @staticmethod
    def get_menu_url():
        raise NotImplementedError
    
    def add_menu(self,context):
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

class ProjectUpload(AbstractSapelliView):
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
        file = request.FILES.get('project')
        try:
            tmp_dir = extract_sapelli(file)
            project = parse_decision_tree(tmp_dir + '/PROJECT.xml')
            geokey_project = create_project(project, request.user, tmp_dir)

            messages.success(self.request, "The project has been created.")

            return redirect(
                'geokey_sapelli:data_upload',
                project_id=geokey_project.id
            )
        except BadZipfile:
            messages.error(
                self.request,
                "The uploaded file is not a Sapelli project file."
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
