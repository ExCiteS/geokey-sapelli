.. image:: https://img.shields.io/pypi/v/geokey-sapelli.svg
    :alt: PyPI Package
    :target: https://pypi.python.org/pypi/geokey-sapelli

.. image:: https://img.shields.io/travis/ExCiteS/geokey-sapelli/master.svg
    :alt: Travis CI Build Status
    :target: https://travis-ci.org/ExCiteS/geokey-sapelli

.. image:: https://img.shields.io/coveralls/ExCiteS/geokey-sapelli/master.svg
    :alt: Coveralls Test Coverage
    :target: https://coveralls.io/r/ExCiteS/geokey-sapelli


geokey-sapelli
==============

Sapelli support in GeoKey. This extension enables user to upload decision trees and data via the admin interfaces.

Installation instructions
-------------------------

*Note:* This guide assumes you have a working `GeoKey <https://github.com/ExCiteS/geokey>`_ installation.

1. Clone the repository:

.. code-block:: console

  git clone https://github.com/ExCiteS/geokey-sapelli.git

2. Install the package:

.. code-block:: console

  cd geokey-sapelli
  pip install -e .

3. Go to your GeoKey installation and edit ``settings.py`` file (usually in ``local_settings\``):

  - Add ``'geokey_sapelli',`` to the `INSTALLED_APPS` list.
  - Add the absolute path to the Sapelli jar file: ``SAPELLI_JAR = '/path/to/sapelli-collector-cmdln-2.0.0-SNAPSHOT-jar-with-dependencies.jar'``

4. To use the extension via the API, first register a new OAuth application with Authorisation type *password*. You will then get the Client ID. Add the Client ID to your ``settings.py`` (usually in ``local_settings\``) as follows:

.. code-block:: console

  SAPELLI_CLIENT_ID = 'YOUR_CLIENT_ID'

5. Add the data base tables:

.. code-block:: console

  python manage.py migrate geokey_sapelli

6. Restart the server.

7. Open a browser and go to the ``/admin/sapelli/`` path on your GeoKey server (e.g. ``http://localhost:8080``). If you see a page titled "**Sapelli**" you have correctly installed the geokey-sapelli extension.

8. To run tests specific to this extension go to your GeoKey installation folder and run:

.. code-block:: console

  python manage.py test geokey_sapelli
