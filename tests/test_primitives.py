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

import enum
import re
from typing import (
    Dict,
    List,
    Mapping,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import pytest

import py_avro_schema as pas
import py_avro_schema._schemas
from py_avro_schema._testing import assert_schema


def test_str():
    py_type = str
    expected = "string"
    assert_schema(py_type, expected)


def test_str_subclass():
    class PyType(str):
        ...

    expected = {
        "type": "string",
        "namedString": "PyType",
    }
    assert_schema(PyType, expected)


def test_str_subclass_namespaced():
    class PyType(str):
        ...

    expected = {
        "type": "string",
        "namedString": "my_package.my_module.PyType",
    }
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_int():
    py_type = int
    expected = "long"
    assert_schema(py_type, expected)


def test_int_32():
    py_type = int
    expected = "int"
    options = pas.Option.INT_32
    assert_schema(py_type, expected, options=options)


def test_bool():
    py_type = bool
    expected = "boolean"
    assert_schema(py_type, expected)


def test_float():
    py_type = float
    expected = "double"
    assert_schema(py_type, expected)


def test_float_32():
    py_type = float
    expected = "float"
    options = pas.Option.FLOAT_32
    assert_schema(py_type, expected, options=options)


def test_bytes():
    py_type = bytes
    expected = "bytes"
    assert_schema(py_type, expected)


def test_none():
    py_type = type(None)
    expected = "null"
    assert_schema(py_type, expected)


def test_string_list():
    py_type = List[str]
    expected = {"type": "array", "items": "string"}
    assert_schema(py_type, expected)


def test_int_list():
    py_type = List[int]
    expected = {"type": "array", "items": "long"}
    assert_schema(py_type, expected)


def test_string_tuple():
    py_type = Tuple[str]
    expected = {"type": "array", "items": "string"}
    assert_schema(py_type, expected)


def test_string_sequence():
    py_type = Sequence[str]
    expected = {"type": "array", "items": "string"}
    assert_schema(py_type, expected)


def test_string_mutable_sequence():
    py_type = MutableSequence[str]
    expected = {"type": "array", "items": "string"}
    assert_schema(py_type, expected)


def test_string_list_of_lists():
    py_type = List[List[str]]
    expected = {
        "type": "array",
        "items": {
            "type": "array",
            "items": "string",
        },
    }
    assert_schema(py_type, expected)


def test_string_list_of_dicts():
    py_type = List[Dict[str, str]]
    expected = {
        "type": "array",
        "items": {
            "type": "map",
            "values": "string",
        },
    }
    assert_schema(py_type, expected)


def test_string_dict():
    py_type = Dict[str, str]
    expected = {"type": "map", "values": "string"}
    assert_schema(py_type, expected)


def test_int_dict():
    py_type = Dict[str, int]
    expected = {"type": "map", "values": "long"}
    assert_schema(py_type, expected)


def test_string_dict_int_keys():
    py_type = Dict[int, str]
    with pytest.raises(
        TypeError,
        match=re.escape(
            "Cannot generate Avro mapping schema for Python dictionary typing.Dict[int, str] with non-string keys"
        ),
    ):
        py_avro_schema._schemas.schema(py_type)


def test_string_mapping():
    py_type = Mapping[str, str]
    expected = {"type": "map", "values": "string"}
    assert_schema(py_type, expected)


def test_string_dict_of_dicts():
    py_type = Dict[str, Dict[str, str]]
    expected = {
        "type": "map",
        "values": {
            "type": "map",
            "values": "string",
        },
    }
    assert_schema(py_type, expected)


def test_union_string_int():
    py_type = Union[str, int]
    expected = ["string", "long"]
    assert_schema(py_type, expected)


def test_union_string_string_int():
    py_type = Union[str, str, int]
    expected = ["string", "long"]
    assert_schema(py_type, expected)


def test_union_of_union_string_int():
    py_type = Union[str, Union[str, int]]
    expected = ["string", "long"]
    assert_schema(py_type, expected)


def test_optional_str():
    py_type = Optional[str]
    expected = ["string", "null"]
    assert_schema(py_type, expected)


def test_enum():
    class PyType(enum.Enum):
        RED = "RED"
        GREEN = "GREEN"

    expected = {
        "type": "enum",
        "name": "PyType",
        "symbols": [
            "RED",
            "GREEN",
        ],
        "default": "RED",
    }
    assert_schema(PyType, expected)


def test_enum_namespaced():
    class PyType(enum.Enum):
        RED = "RED"
        GREEN = "GREEN"

    expected = {
        "type": "enum",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "symbols": [
            "RED",
            "GREEN",
        ],
        "default": "RED",
    }
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_enum_deduplicate_values():
    class PyType(enum.Enum):
        RED = "RED"
        GREEN = "GREEN"
        GREEN_ALIAS = "GREEN"

    expected = {
        "type": "enum",
        "name": "PyType",
        "symbols": [
            "RED",
            "GREEN",
        ],
        "default": "RED",
    }
    assert_schema(PyType, expected)


def test_enum_non_string_values():
    class PyType(enum.Enum):
        RED = 0
        GREEN = 1

    with pytest.raises(
        TypeError, match="Avro enum schema members must be strings. <enum 'PyType'> uses {<class 'int'>} values."
    ):
        assert_schema(PyType, {})


def test_enum_docs():
    class PyType(enum.Enum):
        """My PyType"""

        RED = "RED"
        GREEN = "GREEN"

    expected = {
        "type": "enum",
        "name": "PyType",
        "doc": "My PyType",
        "symbols": [
            "RED",
            "GREEN",
        ],
        "default": "RED",
    }
    assert_schema(PyType, expected, do_doc=True)
