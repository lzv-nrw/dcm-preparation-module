from setuptools import setup


setup(
    version="0.2.0",
    name="dcm-preparation-module",
    description="flask app for dcm-preparation-module-containers",
    author="LZV.nrw",
    install_requires=[
        "flask==3.*",
        "PyYAML==6.*",
        "bagit>=1.7.0,<2.0.0",
        "data-plumber-http>=1.0.0,<2",
        "dcm-common[services, db, orchestration]>=3.28.0,<4",
        "dcm-preparation-module-api>=0.1.0,<1",
    ],
    packages=[
        "dcm_preparation_module",
        "dcm_preparation_module.models",
        "dcm_preparation_module.views",
        "dcm_preparation_module.components"
    ],
    extras_require={
        "cors": ["Flask-CORS==4"],
    },
    setuptools_git_versioning={
          "enabled": True,
          "version_file": "VERSION",
          "count_commits_from_version_file": True,
          "dev_template": "{tag}.dev{ccount}",
    },
)
