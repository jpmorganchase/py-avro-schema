import dataclasses

import avro.schema
import orjson

import py_avro_schema as pas


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
