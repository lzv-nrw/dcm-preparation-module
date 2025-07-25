"""
ValidationConfig data-model definition
"""

from typing import Optional
from dataclasses import dataclass

from dcm_common.models import DataModel, JSONObject

from .target import Target
from .operations import BaseOperation, OPERATIONS_INDEX


@dataclass
class PreparationConfig(DataModel):
    """
    PreparationConfig `DataModel`.

    Keyword arguments:
    target -- `Target`-object pointing to IP to be prepared
    baginfo_operations -- list of `BaseOperation`-objects to be performed
                          on the baginfo metadata of the target
                          (default None)
    sig_prop_operations -- list of `BaseOperation`-objects to be performed
                           on the significant properties/PREMIS metadata
                           of the target
                           (default None)
    """

    target: Target
    baginfo_operations: Optional[list[BaseOperation]] = None
    sig_prop_operations: Optional[list[BaseOperation]] = None

    @DataModel.serialization_handler(
        "baginfo_operations", "bagInfoOperations"
    )
    @classmethod
    def baginfo_operations_serialization_handler(cls, value):
        """Performs `baginfo_operations`-serialization."""
        if value is None:
            DataModel.skip()
        return [operation.json for operation in value]

    @DataModel.serialization_handler(
        "sig_prop_operations", "sigPropOperations"
    )
    @classmethod
    def sig_prop_operations_serialization_handler(cls, value):
        """Performs `sig_prop_operations`-serialization."""
        if value is None:
            DataModel.skip()
        return [operation.json for operation in value]

    @classmethod
    def from_json(cls, json: JSONObject):
        """
        Returns `PreparationConfig` initialized with data from `json`.

        Explicit implementation ensures proper handling of
        "operations"-type attributes.
        """
        kwargs = {"target": Target(json["target"]["path"])}

        for name, json_name in [
            ("baginfo_operations", "bagInfoOperations"),
            ("sig_prop_operations", "sigPropOperations"),
        ]:
            if json.get(json_name) is not None:
                kwargs[name] = []
                for operation in json[json_name]:
                    if not isinstance(operation, dict):
                        raise ValueError(
                            "Unexpected type for operation object: "
                            + f"'{operation}'."
                        )
                    if operation.get("type") not in OPERATIONS_INDEX:
                        raise ValueError(
                            f"Got unexpected value of '{operation['type']}' "
                            + f"for {json_name}-operation type while "
                            + "deserializing 'PreparationConfig'."
                        )
                    kwargs[name].append(
                        OPERATIONS_INDEX[operation["type"]].from_json(
                            operation
                        )
                    )

        return cls(**kwargs)
