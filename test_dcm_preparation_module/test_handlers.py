"""
Test module for the `dcm_preparation_module/handlers.py`.
"""

import pytest
from data_plumber_http.settings import Responses

from dcm_preparation_module.models import PreparationConfig
from dcm_preparation_module import handlers


@pytest.fixture(name="preparation_handler")
def _preparation_handler(fixtures):
    return handlers.get_preparation_handler(fixtures)


@pytest.mark.parametrize(
    ("json", "status"),
    (
        pytest_args := [
            ({"no-preparation": None}, 400),
            ({"preparation": {}}, 400),  # missing target
            ({"preparation": {"target": {}}}, 400),  # missing path
            ({"preparation": {"target": {"path": "test-ip_"}}}, 404),
            (  # no operations
                {"preparation": {"target": {"path": "test_ip"}}},
                Responses.GOOD.status,
            ),
            (  # empty bagInfoOperations
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [],
                    },
                },
                Responses.GOOD.status,
            ),
            (  # non-empty bagInfoOperations, good
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "targetField": "field",
                                "value": "some value",
                            },
                            {
                                "type": "overwriteExisting",
                                "targetField": "field",
                                "value": "some value",
                            },
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [
                                    {"regex": "", "value": "some value"}
                                ],
                            },
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": [
                                    {"literal": "", "value": "some value"}
                                ],
                            },
                        ],
                    },
                },
                Responses.GOOD.status,
            ),
            (  # bad/unknown args in bagInfoOperations
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "targetField": "field",
                                "value": "some value",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "unknown",
                                "targetField": "field",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "targetField": "field",
                                "value": "some value",
                                "unknown": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "overwriteExisting",
                                "targetField": "field",
                                "value": "some value",
                                "unknown": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [],
                                "unknown": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad complement
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "value": "some value",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "targetField": "field",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "targetField": None,
                                "value": "some value",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "complement",
                                "targetField": "field",
                                "value": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad overwrite
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "overwriteExisting",
                                "value": "some value",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "overwriteExisting",
                                "targetField": "field",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "overwriteExisting",
                                "targetField": None,
                                "value": "some value",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "overwriteExisting",
                                "targetField": "field",
                                "value": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad findAndReplace
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "items": [],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": None,
                                "items": [],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": None,
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad findAndReplaceItem
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [{}],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [None],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [
                                    {"regex": None, "value": "some value"}
                                ],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [
                                    {
                                        "regex": "",
                                        "value": "some value",
                                        "unknown": None,
                                    }
                                ],
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad findAndReplaceLiteral
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "items": [],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": None,
                                "items": [],
                            }
                        ],
                    },
                },
                # this code differs (probably because the object is the
                # last in line for validation)
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": None,
                            }
                        ],
                    },
                },
                # this code differs (probably because the object is the
                # last in line for validation)
                422,
            ),
            (  # bad findAndReplaceLiteralItem
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": [{}],
                            }
                        ],
                    },
                },
                400,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": [None],
                            }
                        ],
                    },
                },
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": [
                                    {"literal": None, "value": "some value"}
                                ],
                            }
                        ],
                    },
                },
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "bagInfoOperations": [
                            {
                                "type": "findAndReplaceLiteral",
                                "targetField": "field",
                                "items": [
                                    {
                                        "literal": "",
                                        "value": "some value",
                                        "unknown": None,
                                    }
                                ],
                            }
                        ],
                    },
                },
                400,
            ),
            (  # bad type for sigPropOperations
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "sigPropOperations": None,
                    },
                },
                422,
            ),
            (  # empty sigPropOperations
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "sigPropOperations": [],
                    },
                },
                Responses.GOOD.status,
            ),
            (  # non-empty sigPropOperations
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                        "sigPropOperations": [
                            {
                                "type": "complement",
                                "targetField": "field",
                                "value": "some value",
                            },
                            {
                                "type": "overwriteExisting",
                                "targetField": "field",
                                "value": "some value",
                            },
                            {
                                "type": "findAndReplace",
                                "targetField": "field",
                                "items": [
                                    {"regex": "", "value": "some value"}
                                ],
                            },
                        ],
                    },
                },
                Responses.GOOD.status,
            ),
            (  # callbackUrl
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                    },
                    "callbackUrl": None,
                },
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                    },
                    "callbackUrl": "https://lzv.nrw/callback",
                },
                Responses.GOOD.status,
            ),
            (  # token
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                    },
                    "token": None,
                },
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                    },
                    "token": "non-uuid",
                },
                422,
            ),
            (
                {
                    "preparation": {
                        "target": {"path": "test_ip"},
                    },
                    "token": "37ee72d6-80ab-4dcd-a68d-f8d32766c80d",
                },
                Responses.GOOD.status,
            ),
        ]
    ),
    ids=[f"stage {i+1}" for i in range(len(pytest_args))],
)
def test_preparation_handler(preparation_handler, json, status, fixtures):
    "Test `get_preparation_handler`."

    output = preparation_handler.run(json=json)

    assert output.last_status == status
    if status != Responses.GOOD.status:
        print(output.last_message)
    else:
        assert isinstance(output.data.value["preparation"], PreparationConfig)
        assert (
            fixtures
            not in output.data.value["preparation"].target.path.parents
        )
