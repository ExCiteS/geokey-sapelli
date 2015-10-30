import commands
import json
import os
import xml.etree.ElementTree as ET

from zipfile import ZipFile, BadZipfile
from os.path import basename

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from ..models import SapelliProject
from .project_mapper import create_project
from .sapelli_exceptions import (
    SapelliSAPException,
    SapelliXMLException,
    SapelliDuplicateException
)


class SapelliLoaderMixin(object):
    """
    TODO
    """
    def store_file(self, sap_file):
        filename, extension = os.path.splitext(sap_file.name)
        path = default_storage.save(
            'tmp/' + filename + extension,
            ContentFile(sap_file.read())
        )
        return os.path.join(settings.MEDIA_ROOT, path)

    def load(self, sap_file, user):
        try:
            tmp_file = self.store_file(sap_file)
            tmp_dir = extract_sap(sap_file)
            sapelli_project_info = parse_project(tmp_dir + '/PROJECT.xml')

            fingerprint = get_project_fingerprint(tmp_file, tmp_dir)
            sapelli_project_info['sapelli_fingerprint'] = fingerprint

            if SapelliProject.objects.exists_for_contribution_by_sapelli_info(
                    user,
                    sapelli_project_info['sapelli_id'],
                    sapelli_project_info['sapelli_fingerprint']):
                raise SapelliDuplicateException

            geokey_project = create_project(sapelli_project_info, user, tmp_dir)

            # when successful return the SapelliProject object:
            return geokey_project.sapelli_project
        # TODO other exceptions
        except BadZipfile:
            raise SapelliSAPException('Not a valid ZIP file.')


def extract_sap(file):
    """
    Extracts a Sapelli project zip file and returns the path to the directory
    that stores the files.

    Parameters
    ----------
    file : str
        Path to the file

    Returns
    -------
    str
        Path to the extracted files
    """
    outpath = settings.MEDIA_ROOT + '/tmp/' + basename(file.name)

    z = ZipFile(file)
    for name in z.namelist():
        z.extract(name, outpath)
    file.close()

    return outpath


def parse_list_items(list_element, leaf_tag):
    """
    Traverses through the child elements of a choice an returns all leaf
    elements.

    Parameter
    ---------
    list_element : xml.etree.ElementTree.Element
        Choice element that is traversed
    leaf_tag : string
        Tag name of elements that is looked for

    Returns
    -------
    List
        List of all leaf elements
    """
    items = []
    child_items = list_element.findall(leaf_tag)

    if len(child_items) > 0:
        for child in child_items:
            items = items + parse_list_items(child, leaf_tag)
    else:
        items.append({
            'value': list_element.attrib.get('value'),
            'img': list_element.attrib.get('img')
        })

    return items


def parse_base_field(element):
    field = {
        'sapelli_id': element.attrib.get('id'),
        'caption': element.attrib.get('caption'),
        'description': element.attrib.get('description'),
        'required': element.attrib.get('optional') != 'true',
        'truefalse': False
    }
    return field


def parse_text_element(element):
    number_cnt = ['UnsignedInt', 'SignedInt', 'UnsignedFloat', 'SignedFloat']
    field = parse_base_field(element)

    if element.attrib.get('content') in number_cnt:
        field['geokey_type'] = 'NumericField'
    else:
        field['geokey_type'] = 'TextField'

    return field


def parse_orientation_element(element):
    fields = []

    if element.attrib.get('storeAzimuth') != 'false':
        fields.append({
            'sapelli_id': 'Orientation.Azimuth',
            'caption': 'Azimuth',
            'geokey_type': 'NumericField'
        })
    if element.attrib.get('storePitch') != 'false':
        fields.append({
            'sapelli_id': 'Orientation.Pitch',
            'caption': 'Pitch',
            'geokey_type': 'NumericField'
        })
    if element.attrib.get('storeRoll') != 'false':
        fields.append({
            'sapelli_id': 'Orientation.Roll',
            'caption': 'Roll',
            'geokey_type': 'NumericField'
        })

    return fields


def parse_checkbox_element(element):
    field = parse_base_field(element)
    field['geokey_type'] = 'LookupField'
    field['truefalse'] = True
    field['items'] = [
        {'value': 'false'},
        {'value': 'true'}
    ]

    return field


def parse_button_element(element):
    column = element.attrib.get('column')

    if column in ['none', None]:
        return None

    field = parse_base_field(element)

    if column == 'datetime':
        field['geokey_type'] = 'DateTimeField'
    elif column == 'boolean':
        field['geokey_type'] = 'LookupField'
        field['truefalse'] = True
        field['items'] = [
            {'value': 'false'},
            {'value': 'true'}
        ]

    return field


def parse_list(element):
    target_items = dict(
        List='Item',
        MultiList='Item',
        Choice='Choice'
    )
    field = parse_base_field(element)
    field['geokey_type'] = 'LookupField'
    field['items'] = parse_list_items(element, target_items[element.tag])

    return field


def parse_location_element(element):
    field = parse_base_field(element)
    return field


def parse_form(form_xml):
    """
    Parses a form element

    Parameter
    ---------
    form_xml : xml.etree.ElementTree.Element
        Form element that is parsed

    Returns
    -------
    dict
        Parse form containing the id and choices of the form
    """
    form = dict()
    form['sapelli_id'] = form_xml.attrib.get('name')
    if not form['sapelli_id']:
        form['sapelli_id'] = form_xml.attrib.get('id')

    fields = []
    locations = []

    for child in form_xml:
        if child.tag == 'Page':
            page_fields = parse_form(child).get('fields')
            for f in page_fields:
                fields.append(f)

        elif child.tag == 'Location':
            locations.append(parse_location_element(child))

        elif child.attrib.get('noColumn') != 'true':
            if child.tag == 'Text':
                fields.append(parse_text_element(child))

            elif child.tag in ['List', 'MultiList', 'Choice']:
                fields.append(parse_list(child))

            elif child.tag == 'Orientation':
                orientation_fields = parse_orientation_element(child)
                for f in orientation_fields:
                    fields.append(f)

            elif child.tag == 'Check':
                fields.append(parse_checkbox_element(child))

            elif child.tag == 'Button':
                field = parse_button_element(child)
                if field:
                    fields.append(field)

    form['fields'] = fields
    form['locations'] = locations

    return form


def parse_project(project_xml_file):
    """
    Parses a Sapelli XML project description into a native representation.

    Parameters
    ----------
    file : str
        Path to the decision tree file

    Returns
    -------
    dict
        Contains all essential information about the parsed Sapelli project
    """
    sapelli_project_info = dict()

    try:
        tree = ET.parse(project_xml_file)
    except IOError:
        raise SapelliSAPException('SAP file does not contain a PROJECT.xml file')

    root = tree.getroot()

    sapelli_project_info['name'] = root.attrib.get('name')
    sapelli_project_info['sapelli_id'] = int(root.attrib.get('id'))
    sapelli_project_info['forms'] = []

    for child in root:
        if child.tag == 'Form':
            sapelli_project_info['forms'].append(parse_form(child))

    return sapelli_project_info


def get_project_fingerprint(tmp_file, tmp_dir):
    """
    TODO
    """
    command = 'java -cp %s uk.ac.ucl.excites.sapelli.collector.SapColCmdLn -p %s -load "%s" -json' % (
        settings.SAPELLI_JAR,
        tmp_dir,
        tmp_file
    )
    std_output = commands.getstatusoutput(command)[1]
    return json.loads(std_output).get('fingerprint')
