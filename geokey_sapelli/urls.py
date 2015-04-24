from django.conf.urls import patterns, url

from views import ProjectUpload, DataUpload, ProjectList

urlpatterns = patterns(
    '',
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
        name='data_upload')
)
