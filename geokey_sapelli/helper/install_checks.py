import commands
import re

from django.conf import settings

from geokey.applications.models import Application

from .sapelli_exceptions import SapelliException
from .sapelli_loader import get_sapelli_dir_path, get_sapelli_jar_path

MINIMAL_JAVA_VERSION = '1.7.0'


def check_extension():
    # Check if SAPELLI_CLIENT_ID value is set in settings.py:
    try:
        client_id = settings.SAPELLI_CLIENT_ID
    except AttributeError:
        raise SapelliException('no SAPELLI_CLIENT_ID value set in geokey settings.py.')
    # Check if an application is registered with this client_id:
    try:
        Application.objects.get(client_id=client_id, authorization_grant_type='password')
    except Application.DoesNotExist:
        raise SapelliException('geokey_sapelli is not registered as an application (with password authorisation) on the server.')
    # Check if java 1.7.0 or more recent is installed:
    try:
        status_output = commands.getstatusoutput('java -version')
        if(status_output[0] != 0):
            raise SapelliException('java not installed, please install JRE v7 or later.')
        java_version = re.match(r'java version "(?P<java_version>[0-9]+\.[0-9]+\.[0-9]+)_.*', status_output[1]).group('java_version')
        if(java_version < MINIMAL_JAVA_VERSION):
            raise SapelliException('installed version of java is too old (installed: %s, minimum required: %s).' % (java_version, MINIMAL_JAVA_VERSION))
    except BaseException, e:
        raise SapelliException('could not run java command (%s).' % str(e))
    # Check if there is a sapelli working directory:
    get_sapelli_dir_path()  # raises SapelliException
    # Check if we have the sapelli JAR:
    get_sapelli_jar_path()  # raises SapelliException
