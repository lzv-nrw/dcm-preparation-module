"""
PreparationResult data-model definition
"""

from typing import Optional
from pathlib import Path
from dataclasses import dataclass

from dcm_common.models import DataModel


@dataclass
class PreparationResult(DataModel):
    """
    Preparation result `DataModel`

    Keyword arguments:
    path -- path to output directory relative to shared file system
    success -- overall success of the job
    baginfo_metadata -- metadata collected from bag-info.txt
    """

    path: Optional[Path] = None
    success: Optional[bool] = None
    baginfo_metadata: dict[str, list[str]] = None

    @DataModel.serialization_handler("path")
    @classmethod
    def path_serialization_handler(cls, value):
        """Performs `path`-serialization."""
        if value is None:
            DataModel.skip()
        return str(value)

    @DataModel.deserialization_handler("path")
    @classmethod
    def path_deserialization(cls, value):
        """Performs `path`-deserialization."""
        if value is None:
            DataModel.skip()
        return Path(value)

    @DataModel.serialization_handler("baginfo_metadata", "bagInfoMetadata")
    @classmethod
    def baginfo_metadata_serialization_handler(cls, value):
        """Performs `baginfo_metadata`-serialization."""
        if value is None:
            DataModel.skip()
        return value

    @DataModel.deserialization_handler("baginfo_metadata", "bagInfoMetadata")
    @classmethod
    def baginfo_metadata_deserialization(cls, value):
        """Performs `baginfo_metadata`-deserialization."""
        if value is None:
            DataModel.skip()
        return value
