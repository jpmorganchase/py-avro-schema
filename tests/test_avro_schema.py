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

import avro.schema
import orjson

import py_avro_schema as pas


def test_package_has_version():
    assert pas.__version__ is not None


def test_dataclass_string_field():
    @dataclasses.dataclass
    class PyType:
        """My PyType"""

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
        "namespace": "test_avro_schema",
        "doc": "My PyType",
    }
    json_data = pas.generate(PyType)
    assert json_data == orjson.dumps(expected)
    assert avro.schema.parse(json_data)
