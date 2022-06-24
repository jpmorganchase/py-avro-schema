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


:class:`bool`
-------------

Avro schema: ``boolean``


:class:`bytes`
--------------

Avro schema: ``bytes``


:class:`datetime.date`
------------------

| Avro schema: ``int``
| Avro logical type: ``date``


:class:`float`
--------------

Avro schema: ``double``

To output as the 32-bit Avro schema ``float`` instead, use :attr:`py_avro_schema.Option.FLOAT_32`.


:class:`int`
------------

Avro schema: ``long``

To output as the 32-bit Avro schema ``int`` instead, use :attr:`py_avro_schema.Option.INT_32`.


:class:`NoneType`
-----------------

Avro schema: ``null``

This schema is typically used as a "unioned" type where the default value is ``None``.


:class:`str`
------------

Avro schema: ``string``


:class:`str` subclasses ("named strings")
-----------------------------------------

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
------------------

| Avro schema: ``string``
| Avro logical type: ``uuid``