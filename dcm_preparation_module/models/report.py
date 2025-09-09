"""
Report data-model definition
"""

from dataclasses import dataclass, field

from dcm_common.orchestra import Report as BaseReport

from dcm_preparation_module.models.preparation_result import PreparationResult


@dataclass
class Report(BaseReport):
    data: PreparationResult = field(default_factory=PreparationResult)
