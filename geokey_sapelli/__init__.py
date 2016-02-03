from geokey.extensions.base import register


VERSION_PARTS = (0, 7, 1)
__version__ = '.'.join(map(str, VERSION_PARTS))


try:
    register(
        'geokey_sapelli',
        'Sapelli',
        display_admin=True,
        superuser=False,
        version=__version__
    )
except BaseException:
    print 'Please install GeoKey first'
