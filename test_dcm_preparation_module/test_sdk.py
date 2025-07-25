"""
Test module for the package `dcm-preparation-module-sdk`.
"""

from time import sleep

import pytest
from bagit import Bag
import dcm_preparation_module_sdk

from dcm_preparation_module import app_factory
from dcm_preparation_module.views import PreparationView


@pytest.fixture(name="app")
def _app(testing_config):
    testing_config.ORCHESTRATION_AT_STARTUP = True
    return app_factory(testing_config(), as_process=True)


@pytest.fixture(name="default_sdk", scope="module")
def _default_sdk():
    return dcm_preparation_module_sdk.DefaultApi(
        dcm_preparation_module_sdk.ApiClient(
            dcm_preparation_module_sdk.Configuration(
                host="http://localhost:8083"
            )
        )
    )


@pytest.fixture(name="preparation_sdk", scope="module")
def _preparation_sdk():
    return dcm_preparation_module_sdk.PreparationApi(
        dcm_preparation_module_sdk.ApiClient(
            dcm_preparation_module_sdk.Configuration(
                host="http://localhost:8083"
            )
        )
    )


def test_default_ping(
    default_sdk: dcm_preparation_module_sdk.DefaultApi, app, run_service
):
    """Test default endpoint `/ping-GET`."""

    run_service(app, port=8083, probing_path="ready")

    response = default_sdk.ping()

    assert response == "pong"


def test_default_status(
    default_sdk: dcm_preparation_module_sdk.DefaultApi, app, run_service
):
    """Test default endpoint `/status-GET`."""

    run_service(app, port=8083, probing_path="ready")

    response = default_sdk.get_status()

    assert response.ready


def test_default_identify(
    default_sdk: dcm_preparation_module_sdk.DefaultApi,
    app,
    run_service,
    testing_config,
):
    """Test default endpoint `/identify-GET`."""

    run_service(app, port=8083, probing_path="ready")

    response = default_sdk.identify()

    assert response.to_dict() == testing_config().CONTAINER_SELF_DESCRIPTION


def test_prepare_report_minimal(
    preparation_sdk: dcm_preparation_module_sdk.PreparationApi,
    app,
    run_service,
    testing_config,
):
    """
    Minimal test for endpoints `/prepare-POST` and `/report-GET`
    (no operations).
    """

    run_service(app, port=8083, probing_path="ready")

    submission = preparation_sdk.prepare(
        {"preparation": {"target": {"path": str("test_ip")}}}
    )

    while True:
        try:
            report = preparation_sdk.get_report(token=submission.value)
            break
        except dcm_preparation_module_sdk.exceptions.ApiException as e:
            assert e.status == 503
            sleep(0.1)
    assert report.data.success
    assert (testing_config().FS_MOUNT_POINT / report.data.path).is_dir()


def test_prepare_report_404(
    preparation_sdk: dcm_preparation_module_sdk.PreparationApi,
    app,
    run_service,
):
    """Test prepare endpoint `/report-GET` without previous submission."""

    run_service(app, port=8083, probing_path="ready")

    with pytest.raises(
        dcm_preparation_module_sdk.rest.ApiException
    ) as exc_info:
        preparation_sdk.get_report(token="some-token")
    assert exc_info.value.status == 404


@pytest.mark.parametrize(
    ("baginfo_operations", "expected_error"),
    [
        (
            [{}],
            dcm_preparation_module_sdk.exceptions.BadRequestException,
        ),
        (
            [
                {
                    "type": "unknown",
                }
            ],
            ValueError,
        ),
        (
            [
                {
                    "type": "complement",
                }
            ],
            ValueError,
        ),
        (
            [
                {
                    "type": "complement",
                    "targetField": "field",
                    "value": "new value",
                },
                {
                    "type": "overwriteExisting",
                    "targetField": "field",
                    "value": "overwritten value",
                },
                {
                    "type": "findAndReplace",
                    "targetField": "field",
                    "items": [
                        {"regex": r"[a-z\s]*", "value": "replaced value"}
                    ],
                },
                {
                    "type": "findAndReplaceLiteral",
                    "targetField": "field",
                    "items": [
                        {"literal": " replaced value ", "value": "final value"}
                    ],
                },
            ],
            None,
        ),
    ],
    ids=[
        "missing-type",
        "unknown-type",
        "missing-args",
        "ok",
    ],
)
def test_prepare_sdk_patch_broken_operations_anyof(
    preparation_sdk: dcm_preparation_module_sdk.PreparationApi,
    app,
    run_service,
    baginfo_operations,
    expected_error,
    testing_config,
):
    """
    Test endpoint `/prepare-POST` for functionality of the applied sdk patch
    `broken_operations_anyof`.
    """

    run_service(app, port=8083, probing_path="ready")

    if expected_error is not None:
        with pytest.raises(expected_error):
            preparation_sdk.prepare(
                {
                    "preparation": {
                        "target": {"path": str("test_ip")},
                        "bagInfoOperations": baginfo_operations,
                    }
                }
            )
    else:
        submission = preparation_sdk.prepare(
            {
                "preparation": {
                    "target": {"path": str("test_ip")},
                    "bagInfoOperations": baginfo_operations,
                }
            }
        )
        while True:
            try:
                report = preparation_sdk.get_report(token=submission.value)
                break
            except dcm_preparation_module_sdk.exceptions.ApiException as e:
                assert e.status == 503
                sleep(0.1)
        assert report.data.success
        assert (testing_config().FS_MOUNT_POINT / report.data.path).is_dir()
        output_bag = Bag(str(testing_config.FS_MOUNT_POINT / report.data.path))
        assert output_bag.is_valid()


def test_prepare_report_multiple_baginfo_operations(
    preparation_sdk: dcm_preparation_module_sdk.PreparationApi,
    app,
    run_service,
    testing_config,
    fixtures,
):
    """
    Test endpoints `/prepare-POST` and `/report-GET` for multiple
    bagInfoOperations.
    """

    run_service(app, port=8083, probing_path="ready")

    submission = preparation_sdk.prepare(
        {
            "preparation": {
                "target": {"path": str("test_ip")},
                "bagInfoOperations": [
                    {
                        "type": "complement",
                        "targetField": "a",
                        "value": "new value",
                    },
                    {
                        "type": "overwriteExisting",
                        "targetField": "a",
                        "value": "overwritten value",
                    },
                    {
                        "type": "findAndReplace",
                        "targetField": "a",
                        "items": [
                            {"regex": r"[a-z\s]*", "value": "replaced value"}
                        ],
                    },
                    {
                        "type": "findAndReplaceLiteral",
                        "targetField": "a",
                        "items": [
                            {
                                "literal": " replaced value ",
                                "value": "final value",
                            }
                        ],
                    },
                ],
            }
        }
    )

    while True:
        try:
            report = preparation_sdk.get_report(token=submission.value)
            break
        except dcm_preparation_module_sdk.exceptions.ApiException as e:
            assert e.status == 503
            sleep(0.1)

    assert report.data.success

    assert (testing_config().FS_MOUNT_POINT / report.data.path).is_dir()
    input_bag = Bag(str(fixtures / "test_ip"))
    output_bag = Bag(str(testing_config.FS_MOUNT_POINT / report.data.path))
    assert output_bag.is_valid()

    assert "a" in output_bag.info
    assert "a" not in input_bag.info
    assert output_bag.info["a"] == "final value"


def test_prepare_report_multiple_sig_prop_operations(
    preparation_sdk: dcm_preparation_module_sdk.PreparationApi,
    app,
    run_service,
    testing_config,
    fixtures,
):
    """
    Test endpoints `/prepare-POST` and `/report-GET` for multiple
    sigPropOperations.
    """

    run_service(app, port=8083, probing_path="ready")

    submission = preparation_sdk.prepare(
        {
            "preparation": {
                "target": {"path": str("test_ip")},
                "sigPropOperations": [
                    {
                        "type": "complement",
                        "targetField": "structure",
                        "value": "new value",
                    },
                    {
                        "type": "overwriteExisting",
                        "targetField": "structure",
                        "value": "overwritten value",
                    },
                    {
                        "type": "findAndReplace",
                        "targetField": "structure",
                        "items": [
                            {"regex": r"[a-z\s]*", "value": "replaced value"}
                        ],
                    },
                    {
                        "type": "findAndReplaceLiteral",
                        "targetField": "structure",
                        "items": [
                            {
                                "literal": " replaced value ",
                                "value": "final value",
                            }
                        ],
                    },
                ],
            }
        }
    )

    while True:
        try:
            report = preparation_sdk.get_report(token=submission.value)
            break
        except dcm_preparation_module_sdk.exceptions.ApiException as e:
            assert e.status == 503
            sleep(0.1)

    assert report.data.success

    assert (testing_config().FS_MOUNT_POINT / report.data.path).is_dir()
    assert Bag(str(testing_config.FS_MOUNT_POINT / report.data.path)).is_valid()

    input_sigprop = PreparationView.load_significant_properties(
        fixtures / "test_ip" / testing_config.SIGPROP_FILE_PATH,
        testing_config.SIGPROP_PREMIS_NAMESPACE,
    )
    output_sigprop = PreparationView.load_significant_properties(
        testing_config.FS_MOUNT_POINT
        / report.data.path
        / testing_config.SIGPROP_FILE_PATH,
        testing_config.SIGPROP_PREMIS_NAMESPACE,
    )

    assert "structure" not in input_sigprop
    assert "structure" in output_sigprop
    assert output_sigprop["structure"] == "final value"
