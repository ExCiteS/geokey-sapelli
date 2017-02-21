from django.conf.urls import include, url

from rest_framework.urlpatterns import format_suffix_patterns

from geokey_sapelli.views import (
    ProjectUpload,
    DataCSVUpload,
    ProjectList,
    LogsZipView,
    LoginAPI,
    ProjectDescriptionAPI,
    ProjectUploadAPI,
    DataCSVUploadAPI,
    DataLogsDownload,
    FindObservationAPI,
    SAPDownloadAPI,
    SAPDownloadQRLinkAPI,
    SapelliLogsViaPersonalInfo, SapelliLogsViaGeoKeyInfo,
)


exportpatterns = [
    url(
        r'^admin/sapelli/projects/(?P<project_id>[0-9]+)/logs/(?P<file>[\w-]+)$',
        LogsZipView.as_view(),
        name='logs_zip'),
]
archivepatterns = format_suffix_patterns(exportpatterns, allowed=['zip'])

urlpatterns = [
    url(
        r'^', include(archivepatterns)),

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
        r'^admin/sapelli/projects/(?P<project_id>[0-9]+)/csv_upload/$',
        DataCSVUpload.as_view(),
        name='data_csv_upload'),
    url(
        r'^admin/sapelli/projects/(?P<project_id>[0-9]+)/logs/$',
        DataLogsDownload.as_view(),
        name='logs'),

    #
    # API ENDPOINTS
    #

    url(
        r'^api/sapelli/login/$',
        LoginAPI.as_view(),
        name='login_api'),
    url(
        r'^api/sapelli/projects/description/(?P<sapelli_project_id>[0-9]+)/(?P<sapelli_project_fingerprint>-?[0-9]+)/$',
        ProjectDescriptionAPI.as_view(),
        name='project_description_api'),
    url(
        r'^api/sapelli/projects/description/(?P<sapelli_project_id>[0-9]+)/(?P<sapelli_project_fingerprint>-?[0-9]+)/logs/$',
        SapelliLogsViaPersonalInfo.as_view(),
        name='project_logs_api_via_personal_info'),
    url(
        r'^api/sapelli/projects/new/$',
        ProjectUploadAPI.as_view(),
        name='project_upload_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/csv_upload/$',
        DataCSVUploadAPI.as_view(),
        name='data_csv_upload_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/find_observation/(?P<category_id>[0-9]+)/$',
        FindObservationAPI.as_view(),
        name='find_observation_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/sap/$',
        SAPDownloadAPI.as_view(),
        name='sap_download_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/sap_qr_link.png$',
        SAPDownloadQRLinkAPI.as_view(),
        name='sap_download_qr_link_api'),
    url(
        r'^api/sapelli/projects/(?P<project_id>[0-9]+)/logs/$',
        SapelliLogsViaGeoKeyInfo.as_view(),
        name='project_logs_api_via_gk_info'),
]
