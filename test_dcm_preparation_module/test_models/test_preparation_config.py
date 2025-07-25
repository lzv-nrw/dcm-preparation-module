"""Test module for the `PreparationConfig` data model."""

from dcm_common.models.data_model import get_model_serialization_test

from dcm_preparation_module.models import (
    Target,
    PreparationConfig,
    ComplementOperation,
    OverwriteExistingOperation,
    FindAndReplaceOperation,
)


test_preparation_config_json = get_model_serialization_test(
    PreparationConfig,
    (
        ((), {"target": Target(".")}),
        ((), {"target": Target("."), "baginfo_operations": []}),
        ((), {"target": Target("."), "sig_prop_operations": []}),
        (
            (),
            {
                "target": Target("."),
                "baginfo_operations": [
                    ComplementOperation(
                        target_field="target field", value="new value"
                    )
                ],
                "sig_prop_operations": [
                    ComplementOperation(
                        target_field="target field", value="new value"
                    )
                ],
            },
        ),
        (
            (),
            {
                "target": Target("."),
                "baginfo_operations": [
                    OverwriteExistingOperation(
                        target_field="target field", value="new value"
                    ),
                    FindAndReplaceOperation.from_json(
                        {
                            "targetField": "target field",
                            "items": [
                                {"regex": r"regex-1", "value": "new value"},
                                {"regex": r"regex-2", "value": "new value 2"},
                            ],
                        }
                    ),
                ],
                "sig_prop_operations": [
                    OverwriteExistingOperation(
                        target_field="target field", value="new value"
                    ),
                    FindAndReplaceOperation.from_json(
                        {
                            "targetField": "target field",
                            "items": [
                                {"regex": r"regex-1", "value": "new value"},
                                {"regex": r"regex-2", "value": "new value 2"},
                            ],
                        }
                    ),
                ],
            },
        ),
    ),
)
