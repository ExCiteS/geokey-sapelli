VERSION_PARTS = (2, 0, 1)
__version__ = '.'.join(map(str, VERSION_PARTS))


try:
    from geokey.extensions.base import register
    register(
        'geokey_sapelli',
        'Sapelli',
        display_admin=True,
        superuser=False,
        version=__version__
    )
except BaseException:
    print 'Please install GeoKey first'
