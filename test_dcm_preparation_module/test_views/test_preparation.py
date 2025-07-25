"""Test-module for preparation-endpoint."""

from shutil import copytree
from uuid import uuid4

import pytest
from bagit import Bag


@pytest.fixture(name="minimal_request_body")
def _minimal_request_body():
    return {"preparation": {"target": {"path": str("test_ip")}}}


def test_prepare_minimal(
    client, testing_config, minimal_request_body, wait_for_report
):
    """
    Test minimal functionality of /prepare-POST endpoint
    (no operations).
    """

    # submit job
    response = client.post("/prepare", json=minimal_request_body)
    assert client.put("/orchestration?until-idle", json={}).status_code == 200

    assert response.status_code == 201
    assert response.mimetype == "application/json"
    token = response.json["value"]

    # wait until job is completed
    json = wait_for_report(client, token)
    assert json["data"]["success"]
    assert "path" in json["data"]
    assert (testing_config.FS_MOUNT_POINT / json["data"]["path"]).is_dir()
    assert Bag(
        str(testing_config.FS_MOUNT_POINT / json["data"]["path"])
    ).is_valid()


# details of bagInfoOperations are tested in component-tests, here we
# only need test integration of models/handlers/components/views and to
# validate that the MetadataOperator is actually called/Bag is updated
def test_prepare_with_baginfo_operations(
    client,
    testing_config,
    fixtures,
    minimal_request_body,
    wait_for_report,
):
    """
    Test functionality of /prepare-POST endpoint for non-empty
    bagInfoOperations.
    """

    minimal_request_body["preparation"]["bagInfoOperations"] = [
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
            "items": [{"regex": r"[a-z\s]*", "value": "replaced value"}],
        },
        {
            "type": "findAndReplaceLiteral",
            "targetField": "a",
            "items": [
                {"literal": " replaced value ", "value": "final value "}
            ],
        },
    ]

    # submit job
    response = client.post("/prepare", json=minimal_request_body)
    assert client.put("/orchestration?until-idle", json={}).status_code == 200

    assert response.status_code == 201
    assert response.mimetype == "application/json"
    token = response.json["value"]

    # wait until job is completed
    json = wait_for_report(client, token)

    assert json["data"]["success"]

    assert "path" in json["data"]
    assert (testing_config.FS_MOUNT_POINT / json["data"]["path"]).is_dir()
    input_bag = Bag(str(fixtures / "test_ip"))
    output_bag = Bag(str(testing_config.FS_MOUNT_POINT / json["data"]["path"]))
    assert output_bag.is_valid()

    assert "a" in output_bag.info
    assert "a" not in input_bag.info
    assert output_bag.info["a"] == "final value"


# details of sigPropOperations are tested in component-tests, here we
# only need test integration of models/handlers/components/views and to
# validate that the MetadataOperator is actually called/Bag is updated
def test_prepare_with_sig_prop_operations(
    client,
    testing_config,
    minimal_request_body,
    wait_for_report,
):
    """
    Test functionality of /prepare-POST endpoint for non-empty
    sigPropOperations.
    """

    minimal_request_body["preparation"]["sigPropOperations"] = [
        {
            "type": "complement",
            "targetField": "structure",
            "value": "new value",
        },
        {
            "type": "overwriteExisting",
            "targetField": "content",
            "value": "overwritten value",
        },
        {
            "type": "findAndReplace",
            "targetField": "context",
            "items": [{"regex": r"[A-Za-z\.\s]*", "value": "replaced value"}],
        },
        {
            "type": "findAndReplaceLiteral",
            "targetField": "context",
            "items": [
                {"literal": " replaced value ", "value": " final value "}
            ],
        },
    ]

    # submit job
    response = client.post("/prepare", json=minimal_request_body)
    assert client.put("/orchestration?until-idle", json={}).status_code == 200

    assert response.status_code == 201
    assert response.mimetype == "application/json"
    token = response.json["value"]

    # wait until job is completed
    json = wait_for_report(client, token)

    assert json["data"]["success"]

    assert "path" in json["data"]
    assert (testing_config.FS_MOUNT_POINT / json["data"]["path"]).is_dir()
    output_bag = Bag(str(testing_config.FS_MOUNT_POINT / json["data"]["path"]))
    assert output_bag.is_valid()

    assert (
        (
            testing_config.FS_MOUNT_POINT
            / json["data"]["path"]
            / testing_config.SIGPROP_FILE_PATH
        ).read_text(encoding="utf-8")
        == """<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
  <premis:object xsi:type="premis:intellectualEntity">
    <premis:objectIdentifier>
      <premis:objectIdentifierType>Relative path</premis:objectIdentifierType>
      <premis:objectIdentifierValue>../data/</premis:objectIdentifierValue>
    </premis:objectIdentifier>
    <premis:significantProperties>
      <premis:significantPropertiesType>content</premis:significantPropertiesType>
      <premis:significantPropertiesValue>overwritten value</premis:significantPropertiesValue>
    </premis:significantProperties>
    <premis:significantProperties>
      <premis:significantPropertiesType>context</premis:significantPropertiesType>
      <premis:significantPropertiesValue>final value</premis:significantPropertiesValue>
    </premis:significantProperties>
    <premis:significantProperties>
      <premis:significantPropertiesType>appearance</premis:significantPropertiesType>
      <premis:significantPropertiesValue>Original layout, including headings and paragraph breaks, must be preserved for human readability.</premis:significantPropertiesValue>
    </premis:significantProperties>
    <premis:significantProperties>
      <premis:significantPropertiesType>behavior</premis:significantPropertiesType>
      <premis:significantPropertiesValue>Hyperlinks embedded in the document must remain functional and allow navigation to linked resources.</premis:significantPropertiesValue>
    </premis:significantProperties>
    <premis:significantProperties>
      <premis:significantPropertiesType>structure</premis:significantPropertiesType>
      <premis:significantPropertiesValue>new value</premis:significantPropertiesValue>
    </premis:significantProperties>
  </premis:object>
</premis:premis>
"""
    )


# details of sigPropOperations are tested in component-tests, here we
# only need test integration of models/handlers/components/views and to
# validate that the MetadataOperator is actually called/Bag is updated
def test_prepare_with_sig_prop_missing_file(
    client,
    testing_config,
    minimal_request_body,
    wait_for_report,
):
    """
    Test functionality of /prepare-POST endpoint for non-empty
    sigPropOperations and missing significant_properties.xml in original
    IP.
    """

    altered_ip = str(uuid4())

    # make copy
    copytree(
        testing_config.FS_MOUNT_POINT
        / minimal_request_body["preparation"]["target"]["path"],
        (
            testing_config.FS_MOUNT_POINT
            / minimal_request_body["preparation"]["target"]["path"]
        ).parent
        / altered_ip,
    )
    # delete/modify files
    (
        (
            testing_config.FS_MOUNT_POINT
            / minimal_request_body["preparation"]["target"]["path"]
        ).parent
        / altered_ip
        / testing_config.SIGPROP_FILE_PATH
    ).unlink()
    for manifest in ["tagmanifest-sha256.txt", "tagmanifest-sha512.txt"]:
        file = (
            (
                testing_config.FS_MOUNT_POINT
                / minimal_request_body["preparation"]["target"]["path"]
            ).parent
            / altered_ip
            / manifest
        )
        file.write_text(
            "\n".join(
                line
                for line in file.read_text(encoding="utf-8").splitlines()
                if str(testing_config.SIGPROP_FILE_PATH) not in line
            ),
            encoding="utf-8",
        )

    # update request
    minimal_request_body["preparation"]["target"]["path"] = altered_ip
    minimal_request_body["preparation"]["sigPropOperations"] = [
        {
            "type": "complement",
            "targetField": "structure",
            "value": "new value",
        },
    ]

    # submit job
    response = client.post("/prepare", json=minimal_request_body)
    assert client.put("/orchestration?until-idle", json={}).status_code == 200

    assert response.status_code == 201
    assert response.mimetype == "application/json"
    token = response.json["value"]

    # wait until job is completed
    json = wait_for_report(client, token)

    assert json["data"]["success"]

    # file exists
    assert (
        testing_config.FS_MOUNT_POINT
        / json["data"]["path"]
        / testing_config.SIGPROP_FILE_PATH
    ).is_file()
    # file contents are as expected
    assert (
        (
            testing_config.FS_MOUNT_POINT
            / json["data"]["path"]
            / testing_config.SIGPROP_FILE_PATH
        ).read_text(encoding="utf-8")
        == """<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
  <premis:object xsi:type="premis:intellectualEntity">
    <premis:objectIdentifier>
      <premis:objectIdentifierType>Relative path</premis:objectIdentifierType>
      <premis:objectIdentifierValue>../data/</premis:objectIdentifierValue>
    </premis:objectIdentifier>
    <premis:significantProperties>
      <premis:significantPropertiesType>structure</premis:significantPropertiesType>
      <premis:significantPropertiesValue>new value</premis:significantPropertiesValue>
    </premis:significantProperties>
  </premis:object>
</premis:premis>
"""
    )
    # tagmanifests are updated
    assert str(testing_config.SIGPROP_FILE_PATH) in (
        testing_config.FS_MOUNT_POINT
        / json["data"]["path"]
        / "tagmanifest-sha256.txt"
    ).read_text(encoding="utf-8")
