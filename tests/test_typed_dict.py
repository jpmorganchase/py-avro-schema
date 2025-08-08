from typing import TypedDict

from py_avro_schema._testing import assert_schema


def test_typed_dict():
    class User(TypedDict):
        name: str
        age: int

    expected = {
        "type": "record",
        "name": "User",
        "fields": [
            {
                "name": "name",
                "type": "string",
            },
            {"name": "age", "type": "long"},
        ],
    }

    assert_schema(User, expected)

    User = TypedDict("User", {"name": str, "age": int})
    assert_schema(User, expected)


def test_type_dict_nested():
    class Address(TypedDict):
        street: str
        number: int

    class User(TypedDict):
        name: str
        age: int
        address: Address

    expected = {
        "type": "record",
        "name": "User",
        "fields": [
            {
                "name": "name",
                "type": "string",
            },
            {"name": "age", "type": "long"},
            {
                "name": "address",
                "type": {
                    "name": "Address",
                    "type": "record",
                    "fields": [
                        {"name": "street", "type": "string"},
                        {"name": "number", "type": "long"},
                    ],
                },
            },
        ],
    }
    assert_schema(User, expected)
