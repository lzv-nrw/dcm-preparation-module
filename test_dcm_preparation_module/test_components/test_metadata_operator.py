"""Test module for the MetadataOperator-component."""

import pytest

from dcm_preparation_module.components import MetadataOperator
from dcm_preparation_module.models import (
    SetOperation,
    ComplementOperation,
    OverwriteExistingOperation,
    FindAndReplaceOperationItem,
    FindAndReplaceOperation,
    FindAndReplaceLiteralOperationItem,
    FindAndReplaceLiteralOperation,
)


@pytest.fixture(name="mo")
def _mo():
    return MetadataOperator()


@pytest.mark.parametrize(
    ("source_metadata", "operations", "expected_metadata"),
    (
        pytest_args := [
            (  # set
                {"y": "old"},
                [
                    SetOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": "old"},
                [
                    SetOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": ["old-0", "old-1"]},
                [
                    SetOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (  # complement
                {"y": "old"},
                [
                    ComplementOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": "old"},
                [
                    ComplementOperation("new", target_field="x"),
                ],
                {"y": "old", "x": "old"},
            ),
            (
                {"y": "old", "x": ["old-0", "old-1"]},
                [
                    ComplementOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["old-0", "old-1"]},
            ),
            (  # overwrite
                {"y": "old"},
                [
                    OverwriteExistingOperation("new", target_field="x"),
                ],
                {"y": "old"},
            ),
            (
                {"y": "old", "x": "old"},
                [
                    OverwriteExistingOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": ["old-0", "old-1"]},
                [
                    OverwriteExistingOperation("new", target_field="x"),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (  # findAndReplace
                {"y": "old"},
                [
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[FindAndReplaceOperationItem("", "new")],
                    ),
                ],
                {"y": "old"},
            ),
            (
                {"y": "old", "x": "old"},
                [
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(r"[a-z]*", "new"),
                        ],
                    ),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": ["old"]},
                [
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(r"[a-z]*", "new"),
                        ],
                    ),
                ],
                {"y": "old", "x": ["new"]},
            ),
            (
                {"y": "old", "x": ["old", "123", "old-123"]},
                [
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(r"[a-z]*", "new"),
                        ],
                    ),
                ],
                {"y": "old", "x": ["new", "123", "old-123"]},
            ),
            (
                {"y": "old", "x": ["old", "123", "old-123"]},
                [
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(r"[a-z]*", "new-0"),
                            FindAndReplaceOperationItem(r"[0-9]*", "new-1"),
                        ],
                    ),
                ],
                {"y": "old", "x": ["new-0", "new-1", "old-123"]},
            ),
            (
                {},
                [
                    SetOperation(
                        target_field="y", value="old"
                    ),
                    ComplementOperation(target_field="x", value="new"),
                    OverwriteExistingOperation(
                        target_field="x", value="new-overwritten"
                    ),
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(
                                r"new-[a-z]*", "new-replaced"
                            ),
                        ],
                    ),
                ],
                {"y": ["old"], "x": ["new-replaced"]},
            ),
            (
                {},
                [
                    SetOperation(
                        target_field="y", value="old"
                    ),
                    OverwriteExistingOperation(
                        target_field="x", value="new-overwritten"
                    ),
                    ComplementOperation(target_field="x", value="new"),
                    FindAndReplaceOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceOperationItem(
                                r"new-[a-z]*", "new-replaced"
                            ),
                        ],
                    ),
                ],
                {"y": ["old"], "x": ["new"]},
            ),
            (  # findAndReplaceLiteral
                {"y": "old"},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="x",
                        items=[FindAndReplaceLiteralOperationItem("", "new")],
                    ),
                ],
                {"y": "old"},
            ),
            (
                {"y": "old "},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="x",
                        items=[
                            FindAndReplaceLiteralOperationItem("old", "new")
                        ],
                    ),
                ],
                {"y": "old "},
            ),
            (
                {"y": "old"},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="y",
                        items=[
                            FindAndReplaceLiteralOperationItem("old", "new")
                        ],
                    ),
                ],
                {"y": ["new"]},
            ),
            (
                {"y": "\nold\t"},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="y",
                        items=[
                            FindAndReplaceLiteralOperationItem(" old ", "new")
                        ],
                    ),
                ],
                {"y": ["new"]},
            ),
            (
                {"y": "old"},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="y",
                        items=[
                            FindAndReplaceLiteralOperationItem(" old ", "new ")
                        ],
                    ),
                ],
                {"y": ["new"]},
            ),
            (
                {"y": "not\nold\t"},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="y",
                        items=[
                            FindAndReplaceLiteralOperationItem(
                                "not old", "new"
                            )
                        ],
                    ),
                ],
                {"y": ["not\nold\t"]},
            ),
            (
                {"x": "old", "y": ["a", "b"]},
                [
                    FindAndReplaceLiteralOperation(
                        target_field="y",
                        items=[
                            FindAndReplaceLiteralOperationItem("a", "c")
                        ],
                    ),
                ],
                {"x": "old", "y": ["c", "b"]},
            ),
        ]
    ),
    ids=[f"stage {i+1}" for i in range(len(pytest_args))],
)
def test_processing(
    source_metadata, operations, expected_metadata, mo: MetadataOperator
):
    """Test `MetadataOperator.process`."""

    result = mo.process(source_metadata, operations)
    print(result.log.fancy())
    assert result.metadata == expected_metadata
