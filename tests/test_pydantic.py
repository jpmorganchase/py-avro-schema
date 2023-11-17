# Copyright 2022 J.P. Morgan Chase & Co.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import decimal
import uuid
from typing import Annotated, List, Optional

import pydantic
import pytest
import typeguard

import py_avro_schema as pas
from py_avro_schema._testing import assert_schema


def test_string_field():
    class PyType(pydantic.BaseModel):
        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected)


def test_class_annotated():
    class PyType(pydantic.BaseModel):
        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(Annotated[PyType, ...], expected)


def test_string_field_default():
    class PyType(pydantic.BaseModel):
        field_a: str = ""

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
                "default": "",
            }
        ],
    }
    assert_schema(PyType, expected)


def test_string_field_default_wrong_type():
    class PyType(pydantic.BaseModel):
        field_a: str = 1  # That's not valid, because field type is str

    with pytest.raises(typeguard.TypeCheckError, match="int is not an instance of str"):
        assert_schema(PyType, {})


def test_optional_field_default():
    class PyType(pydantic.BaseModel):
        field_a: Optional[str] = None

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": [
                    "null",
                    "string",
                ],
                "default": None,
            }
        ],
    }
    assert_schema(PyType, expected)


def test_list_string_field():
    class PyType(pydantic.BaseModel):
        field_a: List[str]

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "array",
                    "items": "string",
                },
            },
        ],
    }
    assert_schema(PyType, expected)


def test_list_string_field_default():
    class PyType(pydantic.BaseModel):
        field_a: List[str] = []  # Pydantic allows mutable defaults like this

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "array",
                    "items": "string",
                },
                "default": [],
            },
        ],
    }
    assert_schema(PyType, expected)


def test_list_string_field_default_wrong_type():
    class PyType(pydantic.BaseModel):
        field_a: List[str] = [1]  # Pydantic allows mutable defaults like this

    with pytest.raises(typeguard.TypeCheckError, match="item 0 of list is not an instance of str"):
        assert_schema(PyType, {})


def test_field():
    class PyTypeChild(pydantic.BaseModel):
        field_a: str

    class PyType(pydantic.BaseModel):
        field_child: PyTypeChild

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "record",
                    "name": "PyTypeChild",
                    "fields": [
                        {
                            "name": "field_a",
                            "type": "string",
                        },
                    ],
                },
            },
        ],
    }
    assert_schema(PyType, expected)


def test_list_dataclass_field():
    class PyTypeChild(pydantic.BaseModel):
        field_a: str

    class PyType(pydantic.BaseModel):
        field_child: List[PyTypeChild]

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "PyTypeChild",
                        "fields": [
                            {
                                "name": "field_a",
                                "type": "string",
                            },
                        ],
                    },
                },
            },
        ],
    }
    assert_schema(PyType, expected)


def test_repeated_field():
    class PyTypeChild(pydantic.BaseModel):
        field_a: str

    class PyType(pydantic.BaseModel):
        field_child_1: PyTypeChild
        field_child_2: PyTypeChild

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_child_1",
                "type": {
                    "type": "record",
                    "name": "PyTypeChild",
                    "fields": [
                        {
                            "name": "field_a",
                            "type": "string",
                        }
                    ],
                },
            },
            {
                "name": "field_child_2",
                "type": "PyTypeChild",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_self_ref_field():
    class PyType(pydantic.BaseModel):
        field_a: "PyType"

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "PyType",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_class_docs():
    class PyType(pydantic.BaseModel):
        """My PyType"""

        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "doc": "My PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, do_doc=True)


def test_field_docs():
    class PyType(pydantic.BaseModel):
        """My PyType"""

        field_a: str = pydantic.Field(description="My field_a")

    expected = {
        "type": "record",
        "name": "PyType",
        "doc": "My PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
                "doc": "My field_a",
            }
        ],
    }
    assert_schema(PyType, expected, do_doc=True)


def test_uuid():
    py_type = pydantic.UUID4
    expected = {
        "type": "string",
        "logicalType": "uuid",
    }
    assert_schema(py_type, expected)


def test_uuid_field_default():
    class PyType(pydantic.BaseModel):
        field_a: pydantic.UUID4 = pydantic.Field(default_factory=uuid.uuid4)

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "string",
                    "logicalType": "uuid",
                },
                "default": "",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_positive_float_field():
    class PyType(pydantic.BaseModel):
        field_a: pydantic.PositiveFloat

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "double",
            }
        ],
    }
    assert_schema(PyType, expected)


def test_model_inheritance():
    class PyTypeCustomBase(pydantic.BaseModel):
        field_a: str

    class PyType(PyTypeCustomBase):
        field_b: str

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            },
            {
                "name": "field_b",
                "type": "string",
            },
        ],
    }
    assert_schema(PyType, expected)


@pytest.mark.xfail(reason="Forward references in base classes not supported yet")
def test_model_inheritance_self_ref_in_base():
    class PyTypeCustomBase(pydantic.BaseModel):
        field_a: "PyTypeCustomBase"

    class PyType(PyTypeCustomBase):
        field_b: str

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "PyTypeCustomBase",
            },
            {
                "name": "field_b",
                "type": "string",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_field_by_alias():
    class PyType(pydantic.BaseModel):
        field_a: str
        field_b: str = pydantic.Field(..., alias="fieldB")

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            },
            {
                "name": "fieldB",
                "type": "string",
            },
        ],
    }
    assert_schema(PyType, expected, options=pas.Option.USE_FIELD_ALIAS)


def test_field_alias_generator():
    class PyType(pydantic.BaseModel):
        field_a: str

        model_config = {"alias_generator": lambda x: x.upper()}

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "FIELD_A",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, options=pas.Option.USE_FIELD_ALIAS)


def test_annotated_decimal():
    class PyType(pydantic.BaseModel):
        field_a: Annotated[
            decimal.Decimal, pas.DecimalMeta(precision=3, scale=2), pydantic.BeforeValidator(lambda x: x)
        ]

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "bytes",
                    "logicalType": "decimal",
                    "precision": 3,
                    "scale": 2,
                },
            }
        ],
    }
    assert_schema(PyType, expected)


def test_annotated_decimal_in_base():
    class Base(pydantic.BaseModel):
        field_a: Annotated[
            decimal.Decimal, pas.DecimalMeta(precision=3, scale=2), pydantic.BeforeValidator(lambda x: x)
        ]

    class PyType(Base):
        field_b: int

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "bytes",
                    "logicalType": "decimal",
                    "precision": 3,
                    "scale": 2,
                },
            },
            {
                "name": "field_b",
                "type": "long",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_annotated_decimal_overridden():
    class Base(pydantic.BaseModel):
        field_a: Annotated[
            decimal.Decimal, pas.DecimalMeta(precision=3, scale=0), pydantic.BeforeValidator(lambda x: x)
        ]

    class PyType(Base):
        field_a: Annotated[
            decimal.Decimal, pas.DecimalMeta(precision=3, scale=2), pydantic.BeforeValidator(lambda x: x)
        ]

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "bytes",
                    "logicalType": "decimal",
                    "precision": 3,
                    "scale": 2,
                },
            }
        ],
    }
    assert_schema(PyType, expected)
