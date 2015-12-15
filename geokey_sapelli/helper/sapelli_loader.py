import commands
import json
import os
import xml.etree.ElementTree as ET

from zipfile import ZipFile, BadZipfile

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from ..models import SapelliProject
from .project_mapper import create_project
from .sapelli_exceptions import (
    SapelliException,
    SapelliSAPException,
    SapelliXMLException,
    SapelliDuplicateException
)

import geokey_sapelli


def get_sapelli_dir_path():
    """
    Creates the Sapelli working directory.

    Returns
    -------
    str:
        Absolute path to the Sapelli working directory.
    
    Raises
    ------
    SapelliException:
        When the working directory could not be created.
    """
    sapelli_dir_path = default_storage.path(os.path.join('sapelli', '')) # joining with '' adds the trailing / or \
    if not os.path.exists(sapelli_dir_path):
        # Create the directory if it doesn't exist:
        try:
            os.makedirs(sapelli_dir_path)
        except BaseException, e:
            raise SapelliException('Failed to create Sapelli working directory (%s): %s' % (sapelli_dir_path, str(e)))
    return sapelli_dir_path


def load_from_sap(sap_file, user):
    """
    Loads & saves a SapelliProject from the given SAP file.

    Parameters
    ----------
    sap_file : django.core.files.File
        Uploaded (suspected) SAP file.

    Returns
    -------
    SapelliProject:
        SapelliProject instance for the parsed project.
    
    Raises
    ------
    SapelliException:
        In case of a configuration problem.
    SapelliSAPException:
        When project loading fails.
    SapelliDuplicateException:
        When the user already has access to the same project.
    """
    # Check if we got a file at all:
    if sap_file is None:
        raise SapelliSAPException('No file provided.')
    
    # Store copy of file on disk (as it probably is an "in memory" file uploaded in an HTTP request):
    try:
        filename, extension = os.path.splitext(os.path.basename(sap_file.name))
        relative_sap_file_path = default_storage.save(os.path.join(get_sapelli_dir_path(), 'Uploads', '') + filename + extension, ContentFile(sap_file.read()))
        sap_file_path = default_storage.path(relative_sap_file_path)
    except BaseException, e:
        raise SapelliSAPException('Failed to store uploaded file: ' + str(e))

    # The file will be deleted if an exception is raised in this block:
    try:
        # Check if it is a valid SAP file:
        check_sap_file(sap_file_path)
        # Load Sapelli project (extract+parse) using SapColCmdLn Java program:
        sapelli_project_info = get_sapelli_project_info(sap_file_path)
    except BaseException, e:
        try: # Remove possibly dangerous file:
            os.remove(sap_file_path)
        except OSError:
            pass
        raise e

    # Check for duplicates:
    if SapelliProject.objects.exists_for_contribution_by_sapelli_info(
            user,
            sapelli_project_info['sapelli_id'],
            sapelli_project_info['sapelli_fingerprint']):
        raise SapelliDuplicateException

    # Create GeoKey and SapelliProject:
    try:
        geokey_project = create_project(sapelli_project_info, user)
    except BaseException, e:
        raise SapelliSAPException(str(e))

    # When successful return the SapelliProject object:
    return geokey_project.sapelli_project

    
def check_sap_file(sap_file_path):
    """
    Checks if the file at the given path is a valid Sapelli project file.

    Parameters
    ----------
    sap_file_path : str
        Path to (suspected) Sapelli project file.

    Raises
    ------
    SapelliSAPException:
        When the given file does not exist, is not a ZIP archive, or does not contain PROJECT.xml.
    """
    try:
        if not os.path.isfile(sap_file_path):
            raise SapelliSAPException('The file does not exist.')
        # Check if it is a ZIP file:
        zip = ZipFile(sap_file_path) # throws BadZipfile
        # Check if it contains PROJECT.xml:
        zip.getinfo('PROJECT.xml') # throws KeyError
    except BadZipfile:
        raise SapelliSAPException('The file is not a valid Sapelli project file (*.sap, *.excites or *.zip).')
    except KeyError:
        raise SapelliSAPException('The file is not a valid Sapelli project file (ZIP archive does not contain PROJECT.xml file).')
    finally:
        try:
            zip.close()
        except BaseException:
            pass


def get_sapelli_jar_path():
    """
    Determines where the Sapelli jar file is.

    Returns
    -------
    str:
        Absolute path to the Sapelli jar file.
    
    Raises
    ------
    SapelliException:
        When the Sapelli jar file cannot be found.
    """
    # Determine where the Sapelli jar file is expected to be:
    if getattr(settings, 'SAPELLI_JAR', None) is not None:
        # Use path configured in GeoKey settings.py:
        sapelli_jar_path = settings.SAPELLI_JAR
    else:
        # Use default path (as advised in README.rst):
        sapelli_jar_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(geokey_sapelli.__path__[0])),
                'lib',
                'sapelli-collector-cmdln-with-dependencies.jar'))
    
    # Check if the Sapelli jar is actually there:
    if not os.path.isfile(sapelli_jar_path):
        raise SapelliException('Cannot find Sapelli jar file at path: %s' % sapelli_jar_path)
        
    # Return path:
    return sapelli_jar_path
            

def get_sapelli_project_info(sap_file_path):
    """
    Uses the Sapelli Collector cmdlnd client (Java) to extract the SAP file and parse the PROJECT.xml.

    Parameters
    ----------
    sap_file_path : str
        Path to Sapelli project file.

    Returns
    -------
    dict:
        the "sapelli_project_info" dictionary describing the loaded project.
    
    Raises
    ------
    SapelliException:
        When the Sapelli jar file cannot be found,
        the Sapelli working directory cannot be created,
        or when the java command could not be run.
    SapelliSAPException:
        When an error occurs during running of SapColCmdLn, will contain java_stacktrace.
    """
    # Run SapColCmdLn class from the Sapelli jar:
    std_output = None
    try:
        command = 'java -cp %s uk.ac.ucl.excites.sapelli.collector.SapColCmdLn -p %s -load "%s" -geokey' % (
            get_sapelli_jar_path(),
            get_sapelli_dir_path(),
            sap_file_path
        )
        std_output = commands.getstatusoutput(command)[1] # may fail if we somehow can't run java at all(?)
        return json.loads(std_output) #fails if java/SapColCmdLn output is not valid JSON
    except SapelliException, se: # coming from get_sapelli_jar_path or get_sapelli_dir_path
        raise se
    except BaseException, e:
        if std_output is not None:
            raise SapelliSAPException('SapColCmdLn error', java_stacktrace=std_output)
        else:
            raise SapelliException('Command error: ' + str(e))
