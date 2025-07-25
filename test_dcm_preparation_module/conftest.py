from pathlib import Path

import pytest
from dcm_common.services.tests import (
    fs_setup, fs_cleanup, external_service, run_service, wait_for_report
)

from dcm_preparation_module import app_factory
from dcm_preparation_module.config import AppConfig


# define fixture-directory
@pytest.fixture(scope="session", name="fixtures")
def _fixtures():
    return Path("test_dcm_preparation_module/fixtures")


@pytest.fixture(scope="session", name="file_storage")
def _file_storage():
    return Path("test_dcm_preparation_module/file_storage")


@pytest.fixture(scope="session", autouse=True)
def disable_extension_logging():
    """
    Disables the stderr-logging via the helper method `print_status`
    of the `dcm_common.services.extensions`-subpackage.
    """
    # pylint: disable=import-outside-toplevel
    from dcm_common.services.extensions.common import PrintStatusSettings

    PrintStatusSettings.silent = True


@pytest.fixture(name="testing_config")
def _testing_config(file_storage):
    """Returns test-config"""
    # setup config-class
    class TestingConfig(AppConfig):
        ORCHESTRATION_AT_STARTUP = False
        ORCHESTRATION_DAEMON_INTERVAL = 0.001
        ORCHESTRATION_ORCHESTRATOR_INTERVAL = 0.001
        ORCHESTRATION_ABORT_NOTIFICATIONS_STARTUP_INTERVAL = 0.01
        TESTING = True
        FS_MOUNT_POINT = file_storage

    return TestingConfig


@pytest.fixture(name="client")
def _client(testing_config):
    """
    Returns test_client.
    """

    return app_factory(testing_config(), block=True).test_client()
