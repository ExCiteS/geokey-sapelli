.. image:: https://img.shields.io/pypi/v/geokey-sapelli.svg
    :alt: PyPI Package
    :target: https://pypi.python.org/pypi/geokey-sapelli

.. image:: https://img.shields.io/travis/ExCiteS/geokey-sapelli/master.svg
    :alt: Travis CI Build Status
    :target: https://travis-ci.org/ExCiteS/geokey-sapelli

.. image:: https://coveralls.io/repos/ExCiteS/geokey-sapelli/badge.svg?branch=master&service=github
    :alt: Coveralls Test Coverage
    :target: https://coveralls.io/github/ExCiteS/geokey-sapelli?branch=master

geokey-sapelli
==============

Extension for `GeoKey <https://github.com/ExCiteS/geokey>`_ to add support for `Sapelli <https://github.com/ExCiteS/Sapelli>`_. This extension enables users to upload `Sapelli project files <http://wiki.sapelli.org/index.php/Overview>`_ (resulting in corresponding GeoKey projects), and Sapelli-produced data via the admin interface.

Install
-------

geokey-sapelli requires:

- Python version 2.7
- `Java <http://www.oracle.com/technetwork/java/javase/downloads>`_ (JRE or JDK) version 7 or up
- GeoKey version 1.0

Install the geokey-sapelli from PyPI:

.. code-block:: console

    pip install geokey-sapelli

Or from cloned repository:

.. code-block:: console

    cd geokey-sapelli
    pip install -e .

Add the package to installed apps:

.. code-block:: console

    INSTALLED_APPS += (
        ...
        'geokey_sapelli',
    )

Download the latest available version of the `Sapelli Collector CmdLn front-end <https://github.com/ExCiteS/Sapelli/releases>`_ (the file you need looks like ``sapelli-collector-cmdln-X.X.X-XXXXXX-with-dependencies.jar``). Place the file in a folder of your choice (you can rename it as well if you want) and edit the `settings.py` file to add the *absolute* path to the file:

.. code-block:: console

    SAPELLI_JAR = '/path/to/sapelli-collector-cmdln-X.X.X-XXXXXX-with-dependencies.jar'

Register a new application (using the GeoKey admin interface) with authorisation type *password*. Add the generated Client ID to your `settings.py`:

.. code-block:: console

  SAPELLI_CLIENT_ID = 'YOUR_CLIENT_ID'

Migrate the models into the database:

.. code-block:: console

    python manage.py migrate geokey_sapelli

You're now ready to go!

Update
------

Update the geokey-sapelli from PyPI:

.. code-block:: console

    pip install -U geokey-sapelli

Migrate the new models into the database:

.. code-block:: console

    python manage.py migrate geokey_sapelli

Test
----

Run tests:

.. code-block:: console

    python manage.py test geokey_sapelli

Check code coverage:

.. code-block:: console

    pip install coverage
    coverage run --source=geokey_sapelli manage.py test geokey_sapelli
    coverage report -m --omit=*/tests/*,*/migrations/*
