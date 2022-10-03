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

import re
import uuid
from typing import List, Optional

import pydantic
import pytest

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

    with pytest.raises(TypeError, match="type of field field_a must be str; got int instead"):
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


def test_optional_field_default_2():
    class PyType(pydantic.BaseModel):
        field_a: str = None  # In Pydantic you can do this :(

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

    with pytest.raises(TypeError, match=re.escape("type of field field_a[0] must be str; got int instead")):
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
        # Using :mod:`uuid` as the library to generate the ID, then cast to :class:`pydantic.UUID4` to match the type
        # hint. Alternatively, just use plain :class:`uuid.UUID` as the type hint.
        field_a: pydantic.UUID4 = pydantic.Field(default_factory=lambda: pydantic.UUID4(uuid.uuid4().hex))

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
