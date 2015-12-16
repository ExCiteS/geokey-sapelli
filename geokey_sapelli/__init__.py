import pkg_resources # part of setuptools

from geokey.extensions.base import register

# Get installed version:
__version__ = pkg_resources.require(__name__)[0].version

register(
    'geokey_sapelli',
    'Sapelli',
    display_admin=True,
    superuser=False,
    version=__version__
)
