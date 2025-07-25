# Digital Curation Manager - Preparation Module

The 'DCM Preparation Module'-API provides functionality to prepare Information Packages (IPs) for transformation into Submission Information Packages (SIPs).
This repository contains the corresponding Flask app definition.
For the associated OpenAPI-document, please refer to the sibling package [`dcm-preparation-module-api`](https://github.com/lzv-nrw/dcm-preparation-module-api).

The contents of this repository are part of the [`Digital Curation Manager`](https://github.com/lzv-nrw/digital-curation-manager).

## Local install
Make sure to include the extra-index-url `https://zivgitlab.uni-muenster.de/api/v4/projects/9020/packages/pypi/simple` in your [pip-configuration](https://pip.pypa.io/en/stable/cli/pip_install/#finding-packages) to enable an automated install of all dependencies.
Using a virtual environment is recommended.

1. Install with
   ```
   pip install .
   ```
1. Configure service environment to fit your needs ([see here](#environmentconfiguration)).
1. Run app as
   ```
   flask run --port=8080
   ```
1. To manually use the API, either run command line tools like `curl` as, e.g.,
   ```
   curl -X 'POST' \
     'http://localhost:8080/prepare' \
     -H 'accept: application/json' \
     -H 'Content-Type: application/json' \
     -d '{
     "preparation": {
       "target": {
         "path": "jobs/abcde-12345-fghijk-67890"
       }
     }
   }'
   ```
   or run a gui-application, like Swagger UI, based on the OpenAPI-document provided in the sibling package [`dcm-preparation-module-api`](https://github.com/lzv-nrw/dcm-preparation-module-api).

## Docker
Build an image using, for example,
```
docker build -t dcm/preparation-module:dev .
```
Then run with
```
docker run --rm --name=preparation-module -p 8080:80 dcm/preparation-module:dev
```
and test by making a GET-http://localhost:8080/identify request.

For additional information, refer to the documentation [here](https://github.com/lzv-nrw/digital-curation-manager).

## Tests
Install additional dev-dependencies with
```
pip install -r dev-requirements.txt
```
Run unit-tests with
```
pytest -v -s
```

## Environment/Configuration
Service-specific environment variables are

### Prepare
* `PREPARED_IP_OUTPUT` [DEFAULT "pip/"] output directory for storing prepared IPs (relative to `FS_MOUNT_POINT`)

Additionally this service provides environment options for
* `BaseConfig`,
* `OrchestratedAppConfig`, and
* `FSConfig`

as listed [here](https://github.com/lzv-nrw/dcm-common#app-configuration).

# Contributors
* Sven Haubold
* Orestis Kazasidis
* Stephan Lenartz
* Kayhan Ogan
* Michael Rahier
* Steffen Richters-Finger
* Malte Windrath
* Roman Kudinov