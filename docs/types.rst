..
   Copyright 2022 J.P. Morgan Chase & Co.

   Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.
   You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and limitations under the License.


Supported data types
====================

.. seealso::

   Official Avro schema specification: https://avro.apache.org/docs/current/spec.html#schemas


**py-avro-schema** supports the following Python types:


Compound types/structures
-------------------------


:func:`dataclasses.dataclass`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Supports Python classes decorated with :func:`dataclasses.dataclass`.

Avro schema: ``record``

The Avro ``record`` type is a named schema.
**py-avro-schema** uses the Python class name as the schema name.

Dataclass fields with types supported by **py-avro-schema** are output as expected, including population of default values.

Example::

   # File shipping/models.py

   import dataclasses
   from typing import Optional

   @dataclasses.dataclass
   class Ship:
       """A beautiful ship"""

       name: str
       year_launched: Optional[int] = None

Is output as:

.. code-block:: json

   {
     "type": "record",
     "name": "Ship",
     "namespace": "shipping",
     "doc": "A beautiful ship",
     "fields": [
       {
         "name": "name",
         "type": "string"
       },
       {
         "name": "year_launched",
         "type": ["null", "long"],
         "default": null
       }
     ],
   }

Field default values may improve Avro schema evolution and resolution.
To validate that all dataclass fields are specified with a default value, use option :attr:`py_avro_schema.Option.DEFAULTS_MANDATORY`.

The Avro record schema's ``doc`` field is populated from the Python class's docstring.
To *disable* this, pass the option :attr:`py_avro_schema.Option.NO_DOC`.

Recursive or repeated reference to the same Python dataclass is supported. After the first time the schema is output, any subsequent references are by name only.


:class:`pydantic.BaseModel`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Supports Python classes inheriting from `pydantic.BaseModel <https://pydantic-docs.helpmanual.io/usage/models/>`_.

.. (No intersphinx for Pydantic, unfortunately.)

Avro schema: ``record``

The Avro ``record`` type is a named schema.
**py-avro-schema** uses the Python class name as the schema name.

Pydantic model fields with types supported by **py-avro-schema** are output as expected, including population of default values and descriptions.

Example::

   # File shipping/models.py

   import pydantic
   from typing import Optional

   class Ship(pydantic.BaseModel):
       """A beautiful ship"""

       name: str
       year_launched: Optional[int] = pydantic.Field(None, description="When we hit the water")

Is output as:

.. code-block:: json

   {
     "type": "record",
     "name": "Ship",
     "namespace": "shipping",
     "doc": "A beautiful ship",
     "fields": [
       {
         "name": "name",
         "type": "string"
       },
       {
         "name": "year_launched",
         "type": ["null", "long"],
         "default": null,
         "doc": "When we hit the water"
       }
     ],
   }

Field default values may improve Avro schema evolution and resolution.
To validate that all model fields are specified with a default value, use option :attr:`py_avro_schema.Option.DEFAULTS_MANDATORY`.

The Avro record schema's ``doc`` attribute is populated from the Python class's docstring.
For individual model fields, the ``doc`` attribute is taken from the Pydantic field's :attr:`description` attribute.
To *disable* this, pass the option :attr:`py_avro_schema.Option.NO_DOC`.

Recursive or repeated reference to the same Pydantic class is supported. After the first time the schema is output, any subsequent references are by name only.


:class:`typing.Union`
~~~~~~~~~~~~~~~~~~~~~

Avro schema: JSON array of multiple Avro schemas

Union members can be any other type supported by **py-avro-schema**.

When defined as a class field with a **default** value, the union members may be re-ordered to ensure that the first member matches the type of the default value.


Collections
-----------


:class:`typing.Dict[str, typing.Any]`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. seealso::

   For a "normal" Avro ``map`` schema using fully typed Python dictionaries, see :ref:`types::class:`typing.mapping``.


| Avro schema: ``bytes``
| Avro logical type: ``json``

Arbitrary Python dictionaries could be serialized as a ``bytes`` Avro schema by first serializing the data as JSON.
**py-avro-schema** supports this "JSON-in-Avro" approach by adding the **custom** logical type ``json`` to a ``bytes`` schema.

To support JSON serialization as *strings* instead of *bytes*, use :attr:`py_avro_schema.Option.LOGICAL_JSON_STRING`.


:class:`typing.Mapping`
~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``map``

This supports other "generic type" versions of :class:`collections.abc.Mapping`, including :class:`typing.Dict`.

Avro ``map`` schemas support **string** keys only. Map values can be any other Python type supported by **py-avro-schema**. For example, ``Dict[str, int]`` is output as:

.. code-block:: json

   {
     "type": "map",
     "values": "long"
   }


:class:`typing.Sequence`
~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``array``

This supports other "generic type" versions of :class:`collections.abc.Sequence`, including :class:`typing.List`.

Sequence values can be any Python type supported by **py-avro-schema**. For example, ``List[int]`` is output as:

.. code-block:: json

   {
     "type": "array",
     "values": "long"
   }


Simple types
------------


:class:`bool` (and subclasses)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``boolean``


:class:`bytes` (and subclasses)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``bytes``


:class:`datetime.date`
~~~~~~~~~~~~~~~~~~~~~~

| Avro schema: ``int``
| Avro logical type: ``date``


:class:`datetime.datetime`
~~~~~~~~~~~~~~~~~~~~~~~~~~

| Avro schema: ``long``
| Avro logical type: ``timestamp-micros``

To output with millisecond precision instead (logical type ``timestamp-millis``), use :attr:`py_avro_schema.Option.MILLISECONDS`.


:class:`datetime.time`
~~~~~~~~~~~~~~~~~~~~~~

| Avro schema: ``long``
| Avro logical type: ``time-micros``

To output with millisecond precision instead (logical type ``time-millis``), use :attr:`py_avro_schema.Option.MILLISECONDS`.


:class:`datetime.timedelta`
~~~~~~~~~~~~~~~~~~~~~~~~~~~

| Avro schema: ``fixed``
| Avro logical type: ``duration``

The Avro ``fixed`` type is a named schema.
Here, **py-avro-schema** uses the name ``datetime.timedelta``.
The full generated schema looks like this:

.. code-block:: json

   {
     "type": "fixed",
     "name": "datetime.timedelta",
     "size": 12,
     "logicalType": "duration"
   }


:class:`enum.Enum`
~~~~~~~~~~~~~~~~~~

Avro schema: ``enum``

The Avro ``enum`` type is a named schema.
**py-avro-schema** uses the Python class name as the schema name.
Avro enum symbols must be strings.

Example::

   # File shipping/models.py

   import enum

   class ShipType(enum.Enum):
       SAILING_VESSEL = "SAILING_VESSEL"
       MOTOR_VESSEL = "MOTOR_VESSEL"

Outputs as:

.. code-block:: json

   {
     "type": "enum",
     "name": "ShipType",
     "namespace": "shipping",
     "symbols": ["SAILING_VESSEL", "MOTOR_VESSEL"],
     "default": "SAILING_VESSEL"
   }

The default value is taken from the first defined enum symbol and is used to support writer/reader schema resolution.


:class:`float` (and subclasses)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``double``

To output as the 32-bit Avro schema ``float`` instead, use :attr:`py_avro_schema.Option.FLOAT_32`.


:class:`int` (and subclasses)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``long``

To output as the 32-bit Avro schema ``int`` instead, use :attr:`py_avro_schema.Option.INT_32`.


:class:`NoneType`
~~~~~~~~~~~~~~~~~

Avro schema: ``null``

This schema is typically used as a "unioned" type where the default value is ``None``.


:class:`py_avro_schema.DecimalType`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| Avro schema: ``bytes``
| Avro logical type: ``decimal``

:class:`py_avro_schema.DecimalType` is a generic type for standard library :class:`decimal.Decimal` values.
The generic type is used to define the **scale** and **precision** of a field.

For example, a decimal field with precision 4 and scale 2 is defined like this::

   import py_avro_schema as pas

   construction_costs: pas.DecimalType[4, 2]

Values can be assigned like normal, e.g. ``construction_costs = decimal.Decimal("12.34")``.

The Avro schema for the above type is:

.. code-block:: json

   {
     "type": "bytes",
     "logicalType": "decimal",
     "precision": 4,
     "scale": 2
   }


:class:`str`
~~~~~~~~~~~~

Avro schema: ``string``


:class:`str` subclasses ("named strings")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avro schema: ``string``

Python classes inheriting from :class:`str` are converted to Avro ``string`` schemas to support serialization of any arbitrary Python types "as a string value".

Primarily to support *deserialization* of Avro data, a custom property ``namedString`` is added and populated as the schema's namespace followed by the class name.
The custom property is used here since the Avro ``string`` schema is not a "named" schema.
**py-avro-schema** schema uses the same namespace logic as with real named Avro schemas.

Example::

   # file shipping/models.py

   class PortName(str):
        ...

Outputs as:

.. code-block:: json

   {
     "type": "string",
     "namedString": "shipping.PortName"
   }


:class:`uuid.UUID`
~~~~~~~~~~~~~~~~~~

| Avro schema: ``string``
| Avro logical type: ``uuid``
