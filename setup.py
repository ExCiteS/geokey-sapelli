#!/usr/bin/env python

from os.path import join
from setuptools import setup, find_packages


name = 'geokey-sapelli'
version = __import__(name.replace('-', '_')).__version__
repository = join('https://github.com/ExCiteS', name)

setup(
    name=name,
    version=version,
    description='Read Sapelli project and load data from CSVs to GeoKey',
    url=repository,
    download_url=join(repository, 'tarball', version),
    author='ExCiteS',
    author_email='excitesucl@gmail.com',
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*']),
    include_package_data=True,
)
