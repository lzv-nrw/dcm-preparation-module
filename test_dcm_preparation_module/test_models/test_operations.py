"""Test module for operation-data models."""

from dcm_common.models.data_model import get_model_serialization_test

from dcm_preparation_module.models import (
    OperationType,
    SetOperation,
    ComplementOperation,
    OverwriteExistingOperation,
    FindAndReplaceOperationItem,
    FindAndReplaceOperation,
    FindAndReplaceLiteralOperationItem,
    FindAndReplaceLiteralOperation,
)


def test_operation_type_enum():
    """Test enums of class `OperationType`."""
    assert OperationType.COMPLEMENT.value == "complement"
    assert OperationType("complement") == OperationType.COMPLEMENT


test_set_operation_json = get_model_serialization_test(
    SetOperation,
    (
        (
            (),
            {
                "target_field": "target field",
                "value": "new value",
            },
        ),
    ),
)


test_complement_operation_json = get_model_serialization_test(
    ComplementOperation,
    (
        (
            (),
            {
                "target_field": "target field",
                "value": "new value",
            },
        ),
    ),
)


test_overwrite_existing_operation_json = get_model_serialization_test(
    OverwriteExistingOperation,
    (
        (
            (),
            {
                "target_field": "target field",
                "value": "new value",
            },
        ),
    ),
)


test_find_and_replace_operation_item_json = get_model_serialization_test(
    FindAndReplaceOperationItem,
    (
        (
            (),
            {
                "regex": r"regex-1",
                "value": "new value",
            },
        ),
    ),
)


test_find_and_replace_operation_json = get_model_serialization_test(
    FindAndReplaceOperation,
    (
        (
            (),
            {
                "target_field": "target field",
                "items": [],
            },
        ),
        (
            (),
            {
                "target_field": "target field",
                "items": [
                    FindAndReplaceOperationItem(r"regex-1", "new value"),
                    FindAndReplaceOperationItem(r"regex-2", "new value 2"),
                ],
            },
        ),
    ),
)


test_find_and_replace_literal_operation_item_json = get_model_serialization_test(
    FindAndReplaceLiteralOperationItem,
    (
        (
            (),
            {
                "literal": "old value",
                "value": "new value",
            },
        ),
    ),
)


test_find_and_replace_literal_operation_json = get_model_serialization_test(
    FindAndReplaceLiteralOperation,
    (
        (
            (),
            {
                "target_field": "target field",
                "items": [],
            },
        ),
        (
            (),
            {
                "target_field": "target field",
                "items": [
                    FindAndReplaceLiteralOperationItem(
                        "old value", "new value"
                    ),
                    FindAndReplaceLiteralOperationItem(
                        "old value 2", "new value 2"
                    ),
                ],
            },
        ),
    ),
)
