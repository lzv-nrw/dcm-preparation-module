"""Test module for the `PreparationResult` data model."""

from pathlib import Path

from dcm_common.models.data_model import get_model_serialization_test

from dcm_preparation_module.models import PreparationResult

test_build_result_json = get_model_serialization_test(
    PreparationResult, (
        ((), {}),
        ((Path("."),), {}),
        ((), {"success": True}),
        ((Path("."), True), {}),
    )
)
