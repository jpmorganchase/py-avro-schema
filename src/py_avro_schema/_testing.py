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


"""
Test functions
"""
import dataclasses
import difflib
from typing import Dict, Type, Union

import avro.schema  # type: ignore
import orjson

import py_avro_schema._schemas


def assert_schema(py_type: Type, expected_schema: Union[str, Dict[str, str]], **kwargs) -> None:
    """Test that the given Python type results in the correct Avro schema"""
    if not kwargs.pop("do_auto_namespace", False):
        kwargs["options"] = kwargs.get("options", py_avro_schema.Option(0)) | py_avro_schema.Option.NO_AUTO_NAMESPACE
    if not kwargs.pop("do_doc", False):
        kwargs["options"] = kwargs.get("options", py_avro_schema.Option(0)) | py_avro_schema.Option.NO_DOC
    actual_schema = py_avro_schema._schemas.schema(py_type, **kwargs)
    expected_schema_json = orjson.dumps(expected_schema, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode()
    actual_schema_json = orjson.dumps(actual_schema, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS).decode()
    if actual_schema != expected_schema:
        print("Expected schema:")
        print(expected_schema_json)
        print("Actual schema:")
        print(actual_schema_json)
        print("Differences:")
        for diff in difflib.unified_diff(
            expected_schema_json.splitlines(),
            actual_schema_json.splitlines(),
            fromfile="expected",
            tofile="actual",
            n=5,
        ):
            print(diff)

    assert actual_schema == expected_schema
    # Assert that we can parse the schema data as a valid Avro schema
    assert avro.schema.make_avsc_object(actual_schema, None)


@dataclasses.dataclass
class PyType:
    """For testing"""

    field_a: str
