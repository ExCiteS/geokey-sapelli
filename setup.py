import os
del os.link

from distutils.core import setup

setup(
    # Application name:
    name="geokey_sapelli",

    # Version number (initial):
    version="0.1.0",

    # Application author details:
    author="Oliver Roick",
    author_email="o.roick@ucl.ac.uk",

    # Packages
    packages=["geokey_sapelli"],

    # Include additional files into the package
    include_package_data=True,

    # long_description=open("README.txt").read(),

    # Dependent packages (distributions)
    install_requires=[

    ],
)
