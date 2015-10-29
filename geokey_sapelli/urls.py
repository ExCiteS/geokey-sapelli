from django.conf.urls import patterns, url

from views import ProjectUpload, DataUpload, ProjectList, ProjectDescriptionAPI, ProjectUploadAPI, Login

urlpatterns = patterns(
    '',

    #
    # ADMIN PAGES
    #

    url(
        r'^admin/sapelli/$',
        ProjectList.as_view(),
        name='index'),
    url(
        r'^admin/sapelli/projects/new$',
        ProjectUpload.as_view(),
        name='project_upload'),
    url(
        r'^admin/sapelli/projects/(?P<project_id>[0-9]+)/upload/$',
        DataUpload.as_view(),
        name='data_upload'),

    #
    # API ENDPOINTS
    #

    url(
        r'^api/sapelli/login/$',
        Login.as_view(),
        name='api_login'),
    url(
        r'^api/sapelli/projects/description/(?P<sapelli_project_id>[0-9]+)/(?P<sapelli_project_fingerprint>[0-9]+)/$',
        ProjectDescriptionAPI.as_view(),
        name='project_description_api'),
    url(
        r'^api/sapelli/projects/new/$',
        ProjectUploadAPI.as_view(),
        name='project_upload_api')
)
