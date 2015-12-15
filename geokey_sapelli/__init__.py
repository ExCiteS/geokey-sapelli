from geokey.extensions.base import register


VERSION = (0, 5, 1)
__version__ = '.'.join(map(str, VERSION))

register(
    'geokey_sapelli',
    'Sapelli',
    display_admin=True,
    superuser=False,
    version=__version__
)
