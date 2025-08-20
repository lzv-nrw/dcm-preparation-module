"""Input handlers for the 'DCM Preparation Module'-app."""

from pathlib import Path

from data_plumber_http import Property, Object, Url, Array, String
from data_plumber_http.settings import Responses
from dcm_common.services.handlers import TargetPath, UUID

from dcm_preparation_module.models import (
    Target,
    PreparationConfig,
    ComplementOperation,
    OverwriteExistingOperation,
    FindAndReplaceOperation,
    FindAndReplaceLiteralOperation,
    OperationType,
)


class DPOperationType(String):
    def make(self, json, loc):
        # perform regular checks for the given json
        operation_type, msg, status = super().make(json, loc)

        # if valid, convert response to OperationType
        if status == Responses.GOOD.status:
            return OperationType(operation_type), msg, status

        # if invalid, set custom message and status:
        # this accounts for otherwise erroneous status codes and messages
        # when an operation with an allowed `operationType`
        # has missing or bad arguments.
        if status == Responses().BAD_VALUE.status:
            return (
                None,
                "Unable to instantiate Operation. Missing or bad argument.",
                400,
            )

        return operation_type, msg, status


def get_preparation_handler(cwd: Path):
    """
    Returns parameterized handler (based on cwd from app_config)
    """

    def get_base_operation_properties(type_: OperationType):
        return {
            Property(
                "type", required=True, validation_only=True
            ): DPOperationType(enum=[type_.value]),
            Property("targetField", required=True): String(),
        }

    complement_operation_object = Object(
        model=lambda **json: ComplementOperation.from_json(json),
        properties=get_base_operation_properties(OperationType.COMPLEMENT)
        | {
            Property("value", required=True): String(),
        },
        accept_only=[
            "type",
            "targetField",
            "value",
        ],
    )

    overwrite_existing_operation_object = Object(
        model=lambda **json: OverwriteExistingOperation.from_json(json),
        properties=get_base_operation_properties(
            OperationType.OVERWRITE_EXISTING
        )
        | {
            Property("value", required=True): String(),
        },
        accept_only=[
            "type",
            "targetField",
            "value",
        ],
    )

    find_and_replace_operation_object = Object(
        model=lambda **json: FindAndReplaceOperation.from_json(json),
        properties=get_base_operation_properties(
            OperationType.FIND_AND_REPLACE
        )
        | {
            Property("items", required=True): Array(
                items=Object(
                    properties={
                        Property("regex", required=True): String(),
                        Property("value", required=True): String(),
                    },
                    accept_only=["regex", "value"],
                )
            ),
        },
        accept_only=[
            "type",
            "targetField",
            "items",
        ],
    )

    find_and_replace_literal_operation_object = Object(
        model=lambda **json: FindAndReplaceLiteralOperation.from_json(json),
        properties=get_base_operation_properties(
            OperationType.FIND_AND_REPLACE_LITERAL
        )
        | {
            Property("items", required=True): Array(
                items=Object(
                    properties={
                        Property("literal", required=True): String(),
                        Property("value", required=True): String(),
                    },
                    accept_only=["literal", "value"],
                )
            ),
        },
        accept_only=[
            "type",
            "targetField",
            "items",
        ],
    )

    return Object(
        properties={
            Property("preparation", required=True): Object(
                model=PreparationConfig,
                properties={
                    Property("target", required=True): Object(
                        model=Target,
                        properties={
                            Property("path", required=True): TargetPath(
                                _relative_to=cwd, cwd=cwd, is_dir=True
                            )
                        },
                        accept_only=["path"],
                    ),
                    Property(
                        "bagInfoOperations",
                        "baginfo_operations",
                        required=False,
                        default=lambda **kwargs: [],
                    ): Array(
                        items=complement_operation_object
                        | overwrite_existing_operation_object
                        | find_and_replace_operation_object
                        | find_and_replace_literal_operation_object
                    ),
                    Property(
                        "sigPropOperations",
                        "sig_prop_operations",
                        required=False,
                        default=lambda **kwargs: [],
                    ): Array(
                        items=complement_operation_object
                        | overwrite_existing_operation_object
                        | find_and_replace_operation_object
                        | find_and_replace_literal_operation_object
                    ),
                },
                accept_only=[
                    "target",
                    "bagInfoOperations",
                    "sigPropOperations",
                ],
            ),
            Property("token"): UUID(),
            Property("callbackUrl", name="callback_url"): Url(
                schemes=["http", "https"]
            ),
        },
        accept_only=["preparation", "token", "callbackUrl"],
    ).assemble()
