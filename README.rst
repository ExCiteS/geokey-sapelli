.. image:: https://img.shields.io/pypi/v/geokey-sapelli.svg
    :alt: PyPI Package
    :target: https://pypi.python.org/pypi/geokey-sapelli

.. image:: https://requires.io/github/ExCiteS/geokey-sapelli/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ExCiteS/geokey-sapelli/requirements/?branch=master

.. image:: https://img.shields.io/travis/ExCiteS/geokey-sapelli/master.svg
    :alt: Travis CI Build Status
    :target: https://travis-ci.org/ExCiteS/geokey-sapelli

.. image:: https://coveralls.io/repos/ExCiteS/geokey-sapelli/badge.svg?branch=master&service=github
    :alt: Coveralls Test Coverage
    :target: https://coveralls.io/github/ExCiteS/geokey-sapelli?branch=master

geokey-sapelli
==============

Extension for `GeoKey <https://github.com/ExCiteS/geokey>`_ to add support for `Sapelli <https://github.com/ExCiteS/Sapelli>`_. This extension enables users to upload `Sapelli project files <http://wiki.sapelli.org/index.php/Overview>`_ (resulting in corresponding GeoKey projects), and Sapelli-produced data via the admin interfaces.

Installation instructions
-------------------------

*Note:* This guide assumes you have a working `GeoKey <https://github.com/ExCiteS/geokey>`_ installation (0.9 or greater), and also have `Java <http://www.oracle.com/technetwork/java/javase/downloads>`_ (JRE or JDK, version 7 or up) installed.


1. Clone the repository:

.. code-block:: console

  git clone https://github.com/ExCiteS/geokey-sapelli.git

2. Install the package:

.. code-block:: console

  cd geokey-sapelli
  pip install -e .

3. Go to your GeoKey installation and edit ``settings.py`` file (usually in ``local_settings\``) to add ``'geokey_sapelli',`` to the ``INSTALLED_APPS`` list.

4. Download the latest available version of the `Sapelli Collector CmdLn front-end <https://github.com/ExCiteS/Sapelli/releases>`_. The file you want looks like ``sapelli-collector-cmdln-X.X.X-XXXXXX-with-dependencies.jar``. You have 2 options regarding the installation of this ``jar`` file:

 - Rename the file to ``sapelli-collector-cmdln-with-dependencies.jar`` and place it in the ``geokey-sapelli/lib`` folder;
 - or, place the file in a folder of your choice (you can rename it as well if you want) and again edit the above-mentioned ``settings.py`` file to add the *absolute* path to the file, like so: ``SAPELLI_JAR = '/path/to/sapelli-collector-cmdln-X.X.X-XXXXXX-with-dependencies.jar'``.

5. To use the extension via the API, first register a new OAuth application with Authorisation type *password*. You will then get the Client ID. Add the Client ID to your ``settings.py`` (usually in ``local_settings\``) as follows:

.. code-block:: console

  SAPELLI_CLIENT_ID = 'YOUR_CLIENT_ID'

6. Add the database tables:

.. code-block:: console

  python manage.py migrate geokey_sapelli

7. Run tests specific to this extension to ensure everything is correctly installed. Go to your GeoKey installation folder and run:

.. code-block:: console

  python manage.py test geokey_sapelli

8. Restart the server.

9. Open a browser and go to the ``/admin/sapelli/`` path on your GeoKey server (e.g. ``http://localhost:8080``). If you see a page titled "**Sapelli**" you have correctly installed the `geokey-sapelli extension <https://github.com/ExCiteS/geokey-sapelli>`_.
