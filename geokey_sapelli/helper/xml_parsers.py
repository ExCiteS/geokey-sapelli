import zipfile
from os.path import basename
import xml.etree.ElementTree as ET

from django.conf import settings


def extract_sapelli(file):
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

    z = zipfile.ZipFile(file)
    for name in z.namelist():
        z.extract(name, outpath)
    file.close()

    return outpath


def parse_choice(choice_xml):
    """
    Traverses through the child elements of a choice an returns all leaf
    elements.

    Parameter
    ---------
    choice_xml : xml.etree.ElementTree.Element
        Choice element that is traversed

    Returns
    -------
    List
        List of all leaf elements
    """
    choices = []
    child_choices = choice_xml.findall('Choice')

    if len(child_choices) > 0:
        for child in child_choices:
            choices = choices + parse_choice(child)
    else:
        choices.append({
            'value': choice_xml.attrib.get('value'),
            'img': choice_xml.attrib.get('img')
        })

    return choices


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
    form['sapelli_id'] = form_xml.attrib.get('id')

    choice_roots = []

    for child in form_xml:
        if child.tag == 'Choice' and child.attrib.get('noColumn') != 'true':
            choice_roots.append({
                'sapelli_id': child.attrib.get('id'),
                'choices': parse_choice(child)
            })

    form['choice_roots'] = choice_roots

    return form


def parse_decision_tree(file):
    """
    Parses a complete descision tree into a native representation.

    Parameters
    ----------
    file : str
        Path to the decision tree file

    Returns
    -------
    dict
        The parsed project
    """
    project = dict()

    tree = ET.parse(file)
    root = tree.getroot()

    project['name'] = root.attrib.get('name')
    project['sapelli_id'] = int(root.attrib.get('id'))
    project['forms'] = []

    for child in root:
        if child.tag == 'Form':
            project['forms'].append(parse_form(child))

    return project
