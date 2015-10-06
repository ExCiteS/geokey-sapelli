# geokey-sapelli

Sapelli support in Geokey. This extension enables user to upload decision trees and data via the admin interfaces.

### Installation instructions

*Note:* This guide assumes you have a working [GeoKey](https://github.com/ExCiteS/geokey) installation.

1. Clone the repository
 ```
    git clone https://github.com/ExCiteS/geokey-sapelli.git
 ```

2. Install the package

    ```
    cd geokey-sapelli
    pip install -e .
    ```

3. Go to your GeoKey installation and edit `settings.py` file (usually in `local_settings\`):

    - Add `'geokey_sapelli',` to the `INSTALLED_APPS` list.
    - Add the absolute path to the Sapelli jar file: `SAPELLI_JAR = '/path/to/sapelli-collector-cmdln-2.0.0-SNAPSHOT-jar-with-dependencies.jar'`

4. Restart the server.

5. Open a browser and go to the `/admin/sapelli/` path on your GeoKey server (e.g. `http://localhost:8080`). If you see a page titled "**Sapelli**" you have correctly installed the geokey-sapelli extension.

6. To run tests specific to this extension go to your GeoKey installation folder and run:
    ```
    python manage.py test geokey_sapelli
    ```
