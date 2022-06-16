..
   Copyright 2022 J.P. Morgan Chase & Co.

   Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
   You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and limitations under the License.


Tutorial
========

This tutorial shows you how to use **py-avro-schema**, step by step.


Define data types and structures
--------------------------------

An example data structure could be defined like this in Python::

    # File shipping/models.py
    import dataclasses


    @dataclasses.dataclass
    class Ship:
        """A beautiful ship"""

        name: str
        year_launched: int

This defines a single type :class:`Ship` with 2 fields: ``name`` (some text) and ``year_launched`` (a number).

The type hints are essential and used by **py-avro-schema** to generate the Avro schema!


Generating the Avro schema
--------------------------

To represent this as a data type, we run the following commands (here we use an interactive Python shell):

>>> import py_avro_schema as pas
>>> import shipping.models
>>> pas.generate(shipping.models.Ship)
b'{"type":"record","name":"Ship","fields":[{"name":"name","type":"string"},{"name":"year_launched","type":"long"}],"namespace":"shipping","doc":"A beautiful ship"}'

The output is the Avro schema as a (binary) JSON string.

If we wanted to, we could format the JSON string a bit nicer:

>>> raw_json = pas.generate(Ship, options=pas.Option.JSON_INDENT_2)
>>> print(raw_json.decode())
{
  "type": "record",
  "name": "Ship",
  "fields": [
    {
      "name": "name",
      "type": "string"
    },
    {
      "name": "year_launched",
      "type": "long"
    }
  ],
  "namespace": "shipping",
  "doc": "A beautiful ship"
}

This human-friendly representation is useful for debugging for example.


Controlling the schema namespace
--------------------------------

Avro named types such as a ``Record`` optionally define a "namespace" to qualify their name.

**py-avro-schema** populates the namespace with the Python *package* name within which the Python type is defined.
The recommended pattern is to define (or import-as) the types into a package's ``__init__.py`` module such that the types are importable from a package as populated in the Avro schema namespace.
This can be really useful for deserializing Avro data into Python objects.

*Disable* automatic namespace population like this:

>>> pas.generate(Ship, options=pas.Option.NO_AUTO_NAMESPACE)
b'{"type":"record","name":"Ship","fields":[{"name":"name","type":"string"},{"name":"year_launched","type":"long"}],"doc":"A beautiful ship"}'

Alternatively, to use the full dotted module name (for example :mod:`shipping.models`) instead of the top-level package name (:mod:`shipping`) use the option :attr:`pas.Option.AUTO_NAMESPACE_MODULE`.
