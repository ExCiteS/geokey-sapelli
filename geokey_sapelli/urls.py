from django.conf.urls import patterns, url

from views import ProjectUpload, DataUpload, ProjectList, LoginAPI, ProjectDescriptionAPI, ProjectUploadAPI, FindObservationAPI

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
        LoginAPI.as_view(),
        name='login_api'),
    url(
        r'^api/sapelli/projects/description/(?P<sapelli_project_id>[0-9]+)/(?P<sapelli_project_fingerprint>[0-9]+)/$',
        ProjectDescriptionAPI.as_view(),
        name='project_description_api'),
    url(
        r'^api/sapelli/projects/new/$',
        ProjectUploadAPI.as_view(),
        name='project_upload_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/find_observation/(?P<category_id>[0-9]+)/(?P<sapelli_record_start_time>[0-9Tt:\-\.+Zz]+)/(?P<sapelli_record_device_id>[0-9]+)/$',
        FindObservationAPI.as_view(),
        name='find_observation_api')
)
