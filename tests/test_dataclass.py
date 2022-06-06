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

import dataclasses
import datetime
import decimal
import enum
import re
from typing import Any, Dict, List, Optional

import pytest

import py_avro_schema as pas
from py_avro_schema._testing import assert_schema


def test_string_field():
    @dataclasses.dataclass
    class PyType:
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


def test_string_field_mandatory_default():
    @dataclasses.dataclass
    class PyType:
        field_a: str

    options = pas.Option.DEFAULTS_MANDATORY
    with pytest.raises(TypeError, match="Default value for field field_a is missing"):
        assert_schema(PyType, {}, options=options)


def test_string_field_default():
    @dataclasses.dataclass
    class PyType:
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


def test_string_field_default_mandatory_default():
    @dataclasses.dataclass
    class PyType:
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
    options = pas.Option.DEFAULTS_MANDATORY
    assert_schema(PyType, expected, options=options)


def test_string_field_default_wrong_type():
    @dataclasses.dataclass
    class PyType:
        field_a: str = None  # That's not valid, because field type is str

    with pytest.raises(TypeError, match="type of field field_a must be str; got NoneType instead"):
        assert_schema(PyType, {})


def test_optional_field_default():
    @dataclasses.dataclass
    class PyType:
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
    @dataclasses.dataclass
    class PyType:
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
    @dataclasses.dataclass
    class PyType:
        field_a: List[str] = dataclasses.field(default_factory=list)

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
    @dataclasses.dataclass
    class PyType:
        field_a: List[str] = dataclasses.field(default_factory=lambda: [1])

    with pytest.raises(TypeError, match=re.escape("type of field field_a[0] must be str; got int instead")):
        assert_schema(PyType, {})


def test_dataclass_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
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
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
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


def test_list_namespaced_dataclass_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
        field_child: List[PyTypeChild]

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "PyTypeChild",
                        "namespace": "my_package.my_module",
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
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_dict_namespaced_dataclass_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
        field_child: Dict[str, PyTypeChild]

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "map",
                    "values": {
                        "type": "record",
                        "name": "PyTypeChild",
                        "namespace": "my_package.my_module",
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
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_unioned_namespaced_dataclass_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
        field_child: Optional[PyTypeChild]

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_child",
                "type": [
                    {
                        "type": "record",
                        "name": "PyTypeChild",
                        "namespace": "my_package.my_module",
                        "fields": [
                            {
                                "name": "field_a",
                                "type": "string",
                            },
                        ],
                    },
                    "null",
                ],
            },
        ],
    }
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_dataclass_repeated_string_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
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


def test_dataclass_repeated_enum_field():
    class PyTypeEnum(enum.Enum):
        RED = "RED"
        GREEN = "GREEN"

    @dataclasses.dataclass
    class PyType:
        field_child_1: PyTypeEnum
        field_child_2: PyTypeEnum

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_child_1",
                "type": {
                    "type": "enum",
                    "name": "PyTypeEnum",
                    "symbols": [
                        "RED",
                        "GREEN",
                    ],
                    "default": "RED",
                },
            },
            {
                "name": "field_child_2",
                "type": "PyTypeEnum",
            },
        ],
    }
    assert_schema(PyType, expected)


def test_self_ref_field():
    @dataclasses.dataclass
    class PyType:
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


def test_namespaced_record():
    @dataclasses.dataclass
    class PyType:
        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_namespaced_record_top_level_package():
    from py_avro_schema._testing import PyType

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "py_avro_schema",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, do_auto_namespace=True)


def test_namespaced_record_exact_module():
    from py_avro_schema._testing import PyType

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "py_avro_schema._testing",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    options = pas.Option.AUTO_NAMESPACE_MODULE
    assert_schema(PyType, expected, options=options, do_auto_namespace=True)


def test_namespaced_record_override():
    @dataclasses.dataclass
    class PyType:
        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, namespace="my_package.my_module", do_auto_namespace=True)


def test_namespaced_dataclass_field():
    @dataclasses.dataclass
    class PyTypeChild:
        field_a: str

    @dataclasses.dataclass
    class PyType:
        field_child: PyTypeChild

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "record",
                    "name": "PyTypeChild",
                    "namespace": "my_package.my_module",
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
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_namespaced_dataclass_field_auto_namespace():
    import py_avro_schema._testing

    @dataclasses.dataclass
    class PyType:
        field_child: py_avro_schema._testing.PyType

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "test_dataclass",  # Defined in current test module
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "record",
                    "name": "PyType",
                    "namespace": "py_avro_schema",  # Defined in py_avro_schema._testing
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
    assert_schema(PyType, expected, do_auto_namespace=True)


def test_namespaced_enum_field():
    class PyTypeEnum(enum.Enum):
        RED = "RED"
        GREEN = "GREEN"

    @dataclasses.dataclass
    class PyType:
        field_child: PyTypeEnum

    expected = {
        "type": "record",
        "name": "PyType",
        "namespace": "my_package.my_module",
        "fields": [
            {
                "name": "field_child",
                "type": {
                    "type": "enum",
                    "name": "PyTypeEnum",
                    "namespace": "my_package.my_module",
                    "symbols": [
                        "RED",
                        "GREEN",
                    ],
                    "default": "RED",
                },
            },
        ],
    }
    assert_schema(PyType, expected, namespace="my_package.my_module")


def test_dict_json_logical_string_field():
    @dataclasses.dataclass
    class PyType:
        field_a: Dict[str, Any] = dataclasses.field(
            metadata={"avro_adapter": {"logical_type": "json"}},
            default_factory=dict,
        )

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "string",
                    "logicalType": "json",
                },
                "default": "{}",
            }
        ],
    }
    options = pas.Option.LOGICAL_JSON_STRING
    assert_schema(PyType, expected, options=options)


def test_dict_json_logical_bytes_field():
    @dataclasses.dataclass
    class PyType:
        field_a: Dict[str, Any] = dataclasses.field(
            metadata={"avro_adapter": {"logical_type": "json"}},
            default_factory=dict,
        )

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "bytes",
                    "logicalType": "json",
                },
                "default": "{}",
            }
        ],
    }
    assert_schema(PyType, expected)


def test_decimal_field_default():
    @dataclasses.dataclass
    class PyType:
        field_a: pas.DecimalType[4, 2] = decimal.Decimal("3.14")

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "bytes",
                    "logicalType": "decimal",
                    "precision": 4,
                    "scale": 2,
                },
                "default": r"\u013a",
            }
        ],
    }
    assert_schema(PyType, expected)


def test_decimal_field_default_precision_too_big():
    @dataclasses.dataclass
    class PyType:
        field_a: pas.DecimalType[4, 2] = decimal.Decimal("123.45")

    with pytest.raises(
        ValueError, match="Default value 123.45 has precision 5 which is greater than the schema's precision 4"
    ):
        assert_schema(PyType, {})


def test_decimal_field_default_scale_too_big():
    @dataclasses.dataclass
    class PyType:
        field_a: pas.DecimalType[4, 2] = decimal.Decimal("1.234")

    with pytest.raises(ValueError, match="Default value 1.234 has scale 3 which is greater than the schema's scale 2"):
        assert_schema(PyType, {})


def test_date_field_default():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.date = datetime.date(1971, 1, 1)

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "int",
                    "logicalType": "date",
                },
                "default": 365,
            }
        ],
    }
    assert_schema(PyType, expected)


def test_time_field_default():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.time = datetime.time(12, 0, 0, tzinfo=datetime.timezone.utc)

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "long",
                    "logicalType": "time-micros",
                },
                "default": 12 * 3_600 * 1_000_000,
            }
        ],
    }
    assert_schema(PyType, expected)


def test_time_field_default_no_tzinfo():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.time = datetime.time(12, 0, 0)

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "long",
                    "logicalType": "time-micros",
                },
                "default": 12 * 3_600 * 1_000_000,
            }
        ],
    }
    assert_schema(PyType, expected)


def test_datetime_field_default():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.datetime = datetime.datetime(1970, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)

    expected = {
        "type": "record",
        "name": "PyType",
        "fields": [
            {
                "name": "field_a",
                "type": {
                    "type": "long",
                    "logicalType": "timestamp-micros",
                },
                "default": 12 * 3_600 * 1_000_000,
            }
        ],
    }
    assert_schema(PyType, expected)


def test_datetime_field_default_no_tzinfo():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.datetime = datetime.datetime(1970, 1, 1, 12, 0, 0)

    with pytest.raises(
        TypeError, match=re.escape("Default datetime.datetime(1970, 1, 1, 12, 0) must be timezone-aware")
    ):
        assert_schema(PyType, {})


def test_timedelta_field_default_():
    @dataclasses.dataclass
    class PyType:
        field_a: datetime.timedelta = datetime.timedelta()

    with pytest.raises(
        ValueError,
        match="Defaults for <class 'py_avro_schema._schemas.TimeDeltaSchema'> not currently supported. Use union with "
        "null-schema instead and default value `None`",
    ):
        assert_schema(PyType, {})


def test_class_docstring():
    @dataclasses.dataclass
    class PyType:
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


def test_class_docstring_multiline():
    @dataclasses.dataclass
    class PyType:
        """
        My PyType
        wrapped

        Some detailed explanation
        """

        field_a: str

    expected = {
        "type": "record",
        "name": "PyType",
        "doc": "My PyType wrapped",
        "fields": [
            {
                "name": "field_a",
                "type": "string",
            }
        ],
    }
    assert_schema(PyType, expected, do_doc=True)
