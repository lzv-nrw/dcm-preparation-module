"""Configuration module for the 'Preparation Module'-app."""

import os
from pathlib import Path
from importlib.metadata import version

import yaml
import dcm_preparation_module_api
from dcm_common.services import FSConfig, OrchestratedAppConfig


class AppConfig(FSConfig, OrchestratedAppConfig):
    """
    Configuration for the 'Preparation Module'-app.
    """

    # ------ PREPARE ------
    PREPARED_IP_OUTPUT = Path(os.environ.get("PREPARED_IP_OUTPUT") or "pip")
    SIGPROP_FILE_PATH = Path("meta/significant_properties.xml")
    SIGPROP_PREMIS_NAMESPACE = "{http://www.loc.gov/premis/v3}"  # parsing only
    SIGPROP_PREMIS_TEMPLATE = """<premis:premis xmlns:premis="http://www.loc.gov/premis/v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/premis/v3 https://www.loc.gov/standards/premis/premis.xsd" version="3.0">
  <premis:object xsi:type="premis:intellectualEntity">
    <premis:objectIdentifier>
      <premis:objectIdentifierType>Relative path</premis:objectIdentifierType>
      <premis:objectIdentifierValue>../data/</premis:objectIdentifierValue>
    </premis:objectIdentifier>
  </premis:object>
</premis:premis>
"""
    SIGPROP_PREMIS_SIGNIFICANT_PROPERTY_PARENT = "object"  # element name from `SIGPROP_PREMIS_TEMPLATE`
    SIGPROP_PREMIS_SIGNIFICANT_PROPERTY_TEMPLATE = """
    <premis:significantProperties xmlns:premis="http://www.loc.gov/premis/v3">
      <premis:significantPropertiesType>{type_}</premis:significantPropertiesType>
      <premis:significantPropertiesValue>{value}</premis:significantPropertiesValue>
    </premis:significantProperties>
    """
    SIGPROP_TYPES = [
        "content",
        "context",
        "appearance",
        "behavior",
        "structure",
    ]

    # ------ IDENTIFY ------
    # generate self-description
    API_DOCUMENT = (
        Path(dcm_preparation_module_api.__file__).parent / "openapi.yaml"
    )
    API = yaml.load(
        API_DOCUMENT.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
    )

    def set_identity(self) -> None:
        super().set_identity()
        self.CONTAINER_SELF_DESCRIPTION["description"] = (
            "This API provides endpoints for preparing IPs "
            + "for SIP-transformation."
        )

        # version
        self.CONTAINER_SELF_DESCRIPTION["version"]["api"] = self.API["info"][
            "version"
        ]
        self.CONTAINER_SELF_DESCRIPTION["version"]["app"] = version(
            "dcm-preparation-module"
        )

        # configuration
        # - settings
        settings = self.CONTAINER_SELF_DESCRIPTION["configuration"]["settings"]
        settings["preparation"] = {
            "output": str(self.PREPARED_IP_OUTPUT),
        }
