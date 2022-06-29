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
Generate Apache Avro schemas for Python types including standard library data-classes and Pydantic data models.

The main API is a single function, :func:`generate`. Its first argument is the Python type or class to generate the Avro
schema for.

.. seealso::

   Data types supported by **py-avro-schema**: :doc:`types`.

"""

import functools
from typing import Optional, Type

import orjson

from py_avro_schema._schemas import JSON_OPTIONS, Option, schema
from py_avro_schema._typing import DecimalType

try:
    from importlib import metadata
except ImportError:  # pragma: no cover
    # Python < 3.8
    import importlib_metadata as metadata  # type: ignore

#: Library version, e.g. 1.0.0, taken from Git tags
__version__ = metadata.version("py-avro-schema")


__all__ = [
    "generate",
    "DecimalType",
    "Option",
]


@functools.lru_cache(maxsize=None)
def generate(
    py_type: Type,
    *,
    namespace: Optional[str] = None,
    options: Option = Option(0),
) -> bytes:
    """
    Return an Avro schema as a JSON-formatted bytestring for a given Python class or instance

    This function is cached and can be called repeatedly with the same arguments without any performance penalty.

    :param py_type:   The Python class to generate a schema for.
    :param namespace: The Avro namespace to add to schemas.
    :param options:   Schema generation options as defined by :class:`Option` enum values. Specify multiple values like
                      this: ``Option.INT_32 | Option.FLOAT_32``.
    """
    schema_dict = schema(py_type, namespace=namespace, options=options)
    json_options = 0
    for opt in JSON_OPTIONS:
        if opt in options:
            json_options |= opt.value
    schema_json = orjson.dumps(schema_dict, option=json_options)
    return schema_json
