#!/usr/bin/env python

from os.path import join
from setuptools import setup, find_packages

# Change geokey_sapelli version here (and here alone!):
VERSION_PARTS = (0, 6, 0)

name = 'geokey-sapelli'
version = '.'.join(map(str, VERSION_PARTS))
repository = join('https://github.com/ExCiteS', name)

def get_install_requires():
    """
    parse requirements.txt, ignore links, exclude comments
    """
    requirements = list()
    for line in open('requirements.txt').readlines():
        # skip to next iteration if comment or empty line
        if line.startswith('#') or line.startswith('git+https') or line == '':
            continue
        # add line to requirements
        requirements.append(line.rstrip())

    return requirements

setup(
    name=name,
    version=version,
    description='Read Sapelli project and load data from CSVs to GeoKey',
    url=repository,
    download_url=join(repository, 'tarball', version),
    author='ExCiteS',
    author_email='excitesucl@gmail.com',
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*']),
    install_requires=get_install_requires(),
    include_package_data=True,
)
