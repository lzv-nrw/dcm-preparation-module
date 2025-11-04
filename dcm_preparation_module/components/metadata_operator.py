"""
This module defines the `BagInfoOperator` component
of the Preparation Module-app.
"""

from typing import Optional
from copy import deepcopy
import re
from dataclasses import dataclass

from dcm_common.models import DataModel
from dcm_common import LoggingContext as Context, Logger

from dcm_preparation_module.models import (
    OperationType,
    BaseOperation,
    SetOperation,
    ComplementOperation,
    OverwriteExistingOperation,
    FindAndReplaceOperation,
    FindAndReplaceLiteralOperation,
)


@dataclass
class ProcessResult(DataModel):
    """
    Data model for the result returned from a call
    to `process` method of MetadataOperator.

    Keyword arguments:
    metadata -- processed metadata after applying the requested operations
    log -- `Logger` object
    """

    metadata: dict[str, str | list[str]]
    log: Logger


class MetadataOperator:
    """
    A `MetadataOperator` can be used to process the source metadata of
    an IP based on a series of operations.
    """

    TAG: str = "Metadata Operator"
    _MSG_FIELD_CHANGED = (
        "Mapping-operation '{type_}' on '{target_field}' changed the value "
        + "from '{pre}' to '{post}'."
    )
    _MSG_FIELD_UNCHANGED = (
        "Mapping-operation '{type_}' on '{target_field}' did not change the "
        + "value of '{pre}'."
    )

    @staticmethod
    def _convert_field_str_to_list(
        metadata: dict[str, str | list[str]], target_field: str
    ) -> None:
        """
        Converts the specified `target_field` to a list in place (if
        existing but not a list).
        """
        if isinstance(metadata.get(target_field), str):
            metadata[target_field] = [metadata[target_field]]

    def _set(
        self,
        metadata: dict[str, str | list[str]],
        operation: SetOperation,
    ) -> None:
        """
        Implements `SetOperation`.

        Modifies `metadata` in place.
        """
        metadata[operation.target_field] = [operation.value]

    def _complement(
        self,
        metadata: dict[str, str | list[str]],
        operation: ComplementOperation,
    ) -> None:
        """
        Implements `ComplementOperation`.

        Modifies `metadata` in place.
        """
        if metadata.get(operation.target_field) is None:
            metadata[operation.target_field] = [operation.value]

    def _overwrite_existing(
        self,
        metadata: dict[str, str | list[str]],
        operation: OverwriteExistingOperation,
    ) -> None:
        """
        Implements `OverwriteExistingOperation`.

        Modifies `metadata` in place.
        """
        if metadata.get(operation.target_field) is not None:
            metadata[operation.target_field] = [operation.value]

    def _find_and_replace(
        self,
        metadata: dict[str, str | list[str]],
        operation: FindAndReplaceOperation,
    ) -> None:
        """
        Implements `FindAndReplaceOperation`.

        Modifies `metadata` in place.
        """
        if metadata.get(operation.target_field) is None:
            return

        self._convert_field_str_to_list(metadata, operation.target_field)

        metadata[operation.target_field] = list(
            map(
                lambda field_value: next(
                    (
                        item.value
                        for item in operation.items
                        if re.fullmatch(item.regex, field_value)
                    ),
                    field_value,
                ),
                metadata[operation.target_field],
            )
        )

    def _find_and_replace_literal(
        self,
        metadata: dict[str, str | list[str]],
        operation: FindAndReplaceLiteralOperation,
    ) -> None:
        """
        Implements `FindAndReplaceLiteralOperation`.

        Modifies `metadata` in place.
        """
        if metadata.get(operation.target_field) is None:
            return

        self._convert_field_str_to_list(metadata, operation.target_field)

        metadata[operation.target_field] = list(
            map(
                lambda field_value: next(
                    (
                        item.value.strip()
                        for item in operation.items
                        if item.literal.strip() == field_value.strip()
                    ),
                    field_value,
                ),
                metadata[operation.target_field],
            )
        )

    def process(
        self,
        source_metadata: dict[str, str | list[str]],
        operations: Optional[list[BaseOperation]] = None,
    ) -> ProcessResult:
        """
        Runs operations.

        Keyword arguments:
        source_metadata -- source metadata to apply the operations to
        operations -- operations to be performed on the source_metadata
                      (default None)
        """
        result = ProcessResult(
            deepcopy(source_metadata), Logger(default_origin=self.TAG)
        )

        if operations is None:
            return result

        for operation in operations:
            pre_op_metadata = result.metadata.get(operation.target_field)
            match operation.type_:
                case OperationType.SET:
                    self._set(result.metadata, operation)
                case OperationType.COMPLEMENT:
                    self._complement(result.metadata, operation)
                case OperationType.OVERWRITE_EXISTING:
                    self._overwrite_existing(result.metadata, operation)
                case OperationType.FIND_AND_REPLACE:
                    self._find_and_replace(result.metadata, operation)
                case OperationType.FIND_AND_REPLACE_LITERAL:
                    self._find_and_replace_literal(result.metadata, operation)
            if pre_op_metadata != result.metadata.get(operation.target_field):
                result.log.log(
                    Context.INFO,
                    body=self._MSG_FIELD_CHANGED.format(
                        type_=operation.type_.value,
                        target_field=operation.target_field,
                        pre=pre_op_metadata,
                        post=result.metadata.get(operation.target_field),
                    ),
                )
            else:
                result.log.log(
                    Context.INFO,
                    body=self._MSG_FIELD_UNCHANGED.format(
                        type_=operation.type_.value,
                        target_field=operation.target_field,
                        pre=pre_op_metadata,
                    ),
                )
        return result
