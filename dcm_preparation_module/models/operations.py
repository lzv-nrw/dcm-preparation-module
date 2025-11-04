"""
Operations data-model definitions
"""

from enum import Enum
from dataclasses import dataclass

from dcm_common.models import DataModel


class OperationType(Enum):
    """Enum class for the operation type."""

    SET = "set"
    COMPLEMENT = "complement"
    OVERWRITE_EXISTING = "overwriteExisting"
    FIND_AND_REPLACE = "findAndReplace"
    FIND_AND_REPLACE_LITERAL = "findAndReplaceLiteral"


class BaseOperation(DataModel):
    """
    Data model for BaseOperation.

    This class should not be instantiated.

    Keyword arguments
    type_ -- operation type
    target_field -- target metadata field
    """

    # used as value for type_
    _TYPE: OperationType

    type_: OperationType
    target_field: str

    # pylint: disable=unused-argument
    def __init__(self, target_field: str, **kwargs) -> None:
        self.type_ = self._TYPE
        self.target_field = target_field

    @DataModel.serialization_handler("type_", "type")
    @classmethod
    def type__serialization_handler(cls, value):
        """Handles `type_`-serialization."""
        return value.value

    @DataModel.deserialization_handler("type_", "type")
    @classmethod
    def type__deserialization_handler(cls, value):
        """Handles `type_`-deserialization."""
        return OperationType(value)

    @DataModel.serialization_handler("target_field", "targetField")
    @classmethod
    def target_field_serialization_handler(cls, value):
        """Handles `target_field`-serialization."""
        return value

    @DataModel.deserialization_handler("target_field", "targetField")
    @classmethod
    def target_field_deserialization_handler(cls, value):
        """Handles `target_field`-deserialization."""
        return value

    @classmethod
    def from_json(cls, json):
        return super().from_json(json | {"type": cls._TYPE})


class SetOperation(BaseOperation):
    """
    Data model for SetOperation.

    Inherits from BaseOperation and sets type_.

    Additional keyword arguments:
    value -- value for the target metadata field
    """

    _TYPE = OperationType.SET
    value: str

    def __init__(self, value: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = value


class ComplementOperation(BaseOperation):
    """
    Data model for ComplementOperation.

    Inherits from BaseOperation and sets type_.

    Additional keyword arguments:
    value -- new value for the target metadata field
    """

    _TYPE = OperationType.COMPLEMENT
    value: str

    def __init__(self, value: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = value


class OverwriteExistingOperation(BaseOperation):
    """
    Data model for OverwriteExistingOperation.

    Inherits from BaseOperation and sets type_.

    Additional keyword arguments:
    value -- new value for the target metadata field
    """

    _TYPE = OperationType.OVERWRITE_EXISTING
    value: str

    def __init__(self, value: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = value


@dataclass
class FindAndReplaceOperationItem(DataModel):
    """Data model for a single item in FindAndReplaceOperation."""

    regex: str
    value: str


class FindAndReplaceOperation(BaseOperation):
    """
    Data model for FindAndReplaceOperation.

    Inherits from BaseOperation and sets type_.

    Additional keyword arguments:
    items -- match-value pairs for replacement
    """

    _TYPE = OperationType.FIND_AND_REPLACE
    items: list[FindAndReplaceOperationItem]

    def __init__(
        self, items: list[FindAndReplaceOperationItem], **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.items = items


@dataclass
class FindAndReplaceLiteralOperationItem(DataModel):
    """Data model for a single item in FindAndReplaceOperation."""

    literal: str
    value: str


class FindAndReplaceLiteralOperation(BaseOperation):
    """
    Data model for FindAndReplaceLiteralOperation.

    Inherits from BaseOperation and sets type_.

    Additional keyword arguments:
    items -- match-value pairs for replacement
    """

    _TYPE = OperationType.FIND_AND_REPLACE_LITERAL
    items: list[FindAndReplaceLiteralOperationItem]

    def __init__(
        self, items: list[FindAndReplaceLiteralOperationItem], **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.items = items


OPERATIONS_INDEX = {
    "set": SetOperation,
    "complement": ComplementOperation,
    "overwriteExisting": OverwriteExistingOperation,
    "findAndReplace": FindAndReplaceOperation,
    "findAndReplaceLiteral": FindAndReplaceLiteralOperation,
}
