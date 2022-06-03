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

import datetime
import uuid

import py_avro_schema as pas
from py_avro_schema._testing import assert_schema


def test_date():
    py_type = datetime.date
    expected = {
        "type": "int",
        "logicalType": "date",
    }
    assert_schema(py_type, expected)


def test_time():
    py_type = datetime.time
    expected = {
        "type": "long",
        "logicalType": "time-micros",
    }
    assert_schema(py_type, expected)


def test_time_milliseconds():
    py_type = datetime.time
    expected = {
        "type": "long",
        "logicalType": "time-millis",
    }
    options = pas.Option.MILLISECONDS
    assert_schema(py_type, expected, options=options)


def test_datetime():
    py_type = datetime.datetime
    expected = {
        "type": "long",
        "logicalType": "timestamp-micros",
    }
    assert_schema(py_type, expected)


def test_datetime_milliseconds():
    py_type = datetime.datetime
    expected = {
        "type": "long",
        "logicalType": "timestamp-millis",
    }
    options = pas.Option.MILLISECONDS
    assert_schema(py_type, expected, options=options)


def test_timedelta():
    py_type = datetime.timedelta
    expected = {
        "type": "fixed",
        "name": "datetime.timedelta",
        "size": 12,
        "logicalType": "duration",
    }
    assert_schema(py_type, expected)


def test_decimal():
    py_type = pas.DecimalType[5, 2]
    expected = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    assert_schema(py_type, expected)


def test_multiple_decimals():
    # Test the magic with _GenericAlias!
    py_type_1 = pas.DecimalType[5, 2]
    expected_1 = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    py_type_2 = pas.DecimalType[3, 1]
    expected_2 = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 3,
        "scale": 1,
    }
    assert_schema(py_type_1, expected_1)
    assert_schema(py_type_2, expected_2)


def test_uuid():
    py_type = uuid.UUID
    expected = {
        "type": "string",
        "logicalType": "uuid",
    }
    assert_schema(py_type, expected)
