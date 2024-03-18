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
Module to generate Avro schemas for Python types/classes
"""

from __future__ import annotations

import abc
import collections.abc
import dataclasses
import datetime
import decimal
import enum
import inspect
import sys
import types
import uuid
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Dict,
    ForwardRef,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import orjson
import typeguard

import py_avro_schema._typing

if TYPE_CHECKING:
    # Pydantic not necessarily required at runtime
    import pydantic
    import pydantic.fields

JSONStr = str
JSONObj = Dict[str, Any]
JSONArray = List[Any]
JSONType = Union[JSONStr, JSONObj, JSONArray]

NamesType = List[str]


class TypeNotSupportedError(TypeError):
    """Error raised when a Avro schema cannot be generated for a given Python type"""


class Option(enum.Flag):
    """
    Schema generation options

    Options can be passed in to the function :func:`py_avro_schema.generate`. Multiple values are specified like this::

       Option.INT_32 | Option.FLOAT_32
    """

    #: Format JSON data using 2 spaces indentation
    JSON_INDENT_2 = orjson.OPT_INDENT_2

    #: Sort keys in JSON data
    JSON_SORT_KEYS = orjson.OPT_SORT_KEYS

    #: Append a newline character at the end of the JSON data
    JSON_APPEND_NEWLINE = orjson.OPT_APPEND_NEWLINE  # type: ignore

    #: Use ``int`` schemas (32-bit) instead of ``long`` schemas (64-bit) for Python :class:`int`.
    INT_32 = enum.auto()

    #: Use ``float`` schemas (32-bit) instead of ``double`` schemas (64-bit) for Python class :class:`float`.
    FLOAT_32 = enum.auto()

    #: Use milliseconds instead of microseconds precision for (date)time schemas
    MILLISECONDS = enum.auto()

    #: Mandate default values to be specified for all dataclass fields. This option may be used to enforce default
    #: values on Avro record fields to support schema evolution/resolution.
    DEFAULTS_MANDATORY = enum.auto()

    #: Model ``Dict[str, Any]`` fields as string schemas instead of byte schemas (with logical type ``json``, to support
    #: JSON serialization inside Avro).
    LOGICAL_JSON_STRING = enum.auto()

    #: Do not populate namespaces automatically based on the package a Python class is defined in.
    NO_AUTO_NAMESPACE = enum.auto()

    #: Automatically populate namespaces using full (dotted) module names instead of top-level package names.
    AUTO_NAMESPACE_MODULE = enum.auto()

    #: Do not populate ``doc`` schema attributes based on Python docstrings
    NO_DOC = enum.auto()

    #: Use the alias specified in a classes ``Field`` instead of the field's name.
    #: This currently only affects Pydantic Models
    USE_FIELD_ALIAS = enum.auto()


JSON_OPTIONS = [opt for opt in Option if opt.name and opt.name.startswith("JSON_")]


def schema(
    py_type: Type,
    namespace: Optional[str] = None,
    names: Optional[NamesType] = None,
    options: Option = Option(0),
) -> JSONType:
    """
    Generate and return an Avro schema for a given Python type

    This function is called recursively, traversing the type tree down to primitive type leaves

    :param py_type:   The type/class to generate the schema for.
    :param namespace: The Avro namespace to add to all named schemas.
    :param names:     Sequence of Avro schema names to track previously defined named schemas.
    :param options:   Schema generation options as defined by :class:`Option` enum values. Specify multiple values like
                      this: ``Option.INT_32 | Option.FLOAT_32``.
    """
    if names is None:
        names = []
    schema_obj = _schema_obj(py_type, namespace=namespace, options=options)
    schema_data = schema_obj.data(names=names)
    return schema_data


def _schema_obj(py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)) -> "Schema":
    """
    Dispatch to relevant schema classes

    :param py_type:   The Python class to generate a schema for.
    :param namespace: The Avro namespace to add to schemas.
    :param options:   Schema generation options.
    """
    # Find concrete Schema subclasses defined in the current module
    # TODO: make this pluggable and accept additional classes
    schema_classes = inspect.getmembers(
        sys.modules[__name__],
        lambda obj: inspect.isclass(obj) and issubclass(obj, Schema) and not inspect.isabstract(obj),
    )
    for _, schema_class in schema_classes:
        # Find the first schema class that handles py_type
        schema_obj = schema_class(py_type, namespace=namespace, options=options)  # type: ignore
        if schema_obj:
            return schema_obj
    raise TypeNotSupportedError(f"Cannot generate Avro schema for Python type {py_type}")


class Schema(abc.ABC):
    """Schema base"""

    def __new__(cls, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        Create an instance of this schema class if it handles py_type

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        if cls.handles_type(py_type):
            return super().__new__(cls)
        else:
            return None

    def __init__(self, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        A schema base

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        self.py_type = py_type
        self.options = options
        self._namespace = namespace  # Namespace override

    @property
    def namespace_override(self) -> Optional[str]:
        """Manually set namespace, if any"""
        return self._namespace

    @property
    def namespace(self) -> Optional[str]:
        """The namespace, taking into account auto-namespace options and any override"""
        if self._namespace is None and Option.NO_AUTO_NAMESPACE not in self.options:
            module = inspect.getmodule(self.py_type)
            if module and module.__name__ != "builtin":
                if Option.AUTO_NAMESPACE_MODULE in self.options:
                    return module.__name__
                else:
                    return module.__name__.split(".", 1)[0]  # top-level package
        return self._namespace  # The override

    @abc.abstractmethod
    def data(self, names: NamesType) -> JSONType:
        """Return the schema data"""

    @classmethod
    @abc.abstractmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""

    def make_default(self, py_default: Any) -> Any:
        """
        Return an Avro schema compliant default value for a given Python value

        Typically the Avro JSON schema default value is the same type as the Python type. But if required, this method
        could be overridden in subclasses.
        """
        return py_default


class PrimitiveSchema(Schema):
    """An Avro primitive schema for a given Python type"""

    # TODO: implement make_default for bool

    primitive_types = [
        # Tuple of (Python type, whether to include subclasses too, Avro schema)
        (bool, True, "boolean"),
        (bytes, True, "bytes"),
        (float, True, "double"),  # Return "double" (64 bit) schema for Python floats by default
        (int, True, "long"),  # Return "long" (64 bit) schema for Python integers by default
        (str, False, "string"),  # :class:`StrSubclassSchema` handles string subclasses
        (type(None), False, "null"),
    ]

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return any(
            _is_class(py_type, type_, include_subclasses=include_subclasses)
            for type_, include_subclasses, _ in cls.primitive_types
        )

    def data(self, names: NamesType) -> JSONStr:
        """Return the schema data"""
        if Option.INT_32 in self.options and issubclass(self.py_type, int):
            # If option is set to use 32 bit integers, return "int" schema instead of "double
            return "int"
        elif Option.FLOAT_32 in self.options and issubclass(self.py_type, float):
            # If option is set to use 32 bit floats, return "float" schema instead of "double"
            return "float"
        else:
            # We're guaranteed a match since :meth:`handles_types` applies first
            return next(
                data
                for type_, include_subclasses, data in self.primitive_types
                if _is_class(self.py_type, type_, include_subclasses=include_subclasses)
            )


class StrSubclassSchema(Schema):
    """An Avro string schema for a Python subclass of str, with a custom property referencing the class' fullname"""

    @classmethod
    def handles_type(cls, py_type: Type[str]) -> bool:
        """Whether this schema class can represent a given Python class"""
        return (
            inspect.isclass(py_type)
            and issubclass(py_type, str)
            and py_type is not str
            # Enums are always modelled as enum schemas, even when subclassing str
            and not issubclass(py_type, enum.Enum)
        )

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        fullname = self.py_type.__name__
        if self.namespace:
            fullname = f"{self.namespace}.{fullname}"
        return {
            "type": "string",
            "namedString": fullname,  # Custom property since "string" is not a named schema in Avro schema spec
        }


class DictAsJSONSchema(Schema):
    """An Avro string schema representing a Python Dict[str, Any] or List[Dict[str, Any]] assuming JSON serialization"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_dict_str_any(py_type) or _is_list_dict_str_any(py_type)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        type_ = "string" if Option.LOGICAL_JSON_STRING in self.options else "bytes"
        return {
            "type": type_,
            "logicalType": "json",
        }

    def make_default(self, py_default: Any) -> str:
        """Return an Avro schema compliant default value for a given Python value"""
        return orjson.dumps(py_default).decode()


class UUIDSchema(Schema):
    """An Avro string schema representing a Python UUID object"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, uuid.UUID)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        return {
            "type": "string",
            "logicalType": "uuid",
        }

    def make_default(self, py_default: uuid.UUID) -> str:
        """
        Return an Avro schema compliant default value for a given Python value

        In case of a UUID, it is difficult to imagine how we could create default values other than an empty string. For
        schema evolution purposes, one might want to specify a default. And in a Python class, one is most likely to
        want a default that actually generates a random UUID.
        """
        return ""


class DateSchema(Schema):
    """An Avro logical type date schema for a given Python date type"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, datetime.date) and not _is_class(py_type, datetime.datetime)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        return {"type": "int", "logicalType": "date"}

    def make_default(self, py_default: datetime.date) -> int:
        """Return an Avro schema compliant default value for a given Python value"""
        return (py_default - datetime.date(1970, 1, 1)).days


class TimeSchema(Schema):
    """An Avro logical type time (microseconds precision) schema for a given Python time type"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, datetime.time)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        logical_type = "time-millis" if Option.MILLISECONDS in self.options else "time-micros"
        type_by_logical_type = {
            "time-millis": "int",
            "time-micros": "long",
        }
        return {"type": type_by_logical_type[logical_type], "logicalType": logical_type}

    def make_default(self, py_default: datetime.time) -> int:
        """Return an Avro schema compliant default value for a given Python value"""
        # Force UTC as we're concerned only about time diffs
        dt1 = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc)
        dt2 = datetime.datetime.combine(datetime.datetime(1, 1, 1), py_default, tzinfo=datetime.timezone.utc)
        return int((dt2 - dt1).total_seconds() * 1e6)


class DateTimeSchema(Schema):
    """An Avro logical type timestamp (microseconds precision) schema for a given Python datetime type"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, datetime.datetime)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        logical_type = "timestamp-millis" if Option.MILLISECONDS in self.options else "timestamp-micros"
        return {"type": "long", "logicalType": logical_type}

    def make_default(self, py_default: datetime.datetime) -> int:
        """Return an Avro schema compliant default value for a given Python value"""
        if not py_default.tzinfo:
            raise TypeError(f"Default {py_default!r} must be timezone-aware")
        return int((py_default - datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)).total_seconds() * 1e6)


class TimeDeltaSchema(Schema):
    """An Avro logical type duration schema for a given Python timedelta type"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, datetime.timedelta)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        return {
            "type": "fixed",
            "name": "datetime.timedelta",
            "size": 12,
            "logicalType": "duration",
        }

    def make_default(self, py_default: datetime.timedelta) -> str:
        """Return an Avro schema compliant default value for a given Python value"""
        raise ValueError(
            f"Defaults for {self.__class__} not currently supported. Use union with null-schema instead and default "
            f"value `None`"
        )


class ForwardSchema(Schema):
    """A forward/circular reference which in Avro is just the schema name"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return isinstance(py_type, (str, ForwardRef))

    def data(self, names: NamesType) -> JSONStr:
        """Return the schema data"""
        if isinstance(self.py_type, str):
            return self.py_type  # In Python you can forward ref using a string literal
        else:
            assert isinstance(self.py_type, ForwardRef)
            return self.py_type.__forward_arg__  # Or using a ForwardRef object containing the same string literal


class DecimalSchema(Schema):
    """
    An Avro bytes, logical decimal schema for a Python :class:`decimal.Decimal`

    For this to work, users must annotate variables with like so::

       >>> import decimal
       >>> from typing import Annotated
       >>> my_decimal: Annotated[decimal.Decimal, (4, 2)] = decimal.Decimal("12.34")
    """

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        # Here we are greedy: we catch any decimal.Decimal. However, data() might fail if the annotation is not correct.
        return (
            _is_class(py_type, decimal.Decimal)  # Using DecimalMeta
            or get_origin(py_type) is decimal.Decimal  # Deprecated: DecimalType
        )

    @classmethod
    def _decimal_meta(cls, py_type: Type) -> py_avro_schema._typing.DecimalMeta:
        """Return a decimal precision and scale for type, if possible"""
        origin = get_origin(py_type)
        args = get_args(py_type)
        if origin is Annotated and args and args[0] is decimal.Decimal:
            # Annotated[decimal.Decimal, pas.DecimalMeta(4, 2)]
            try:
                # At least one of the annotations should be a DecimalMeta object
                (meta,) = (arg for arg in args[1:] if isinstance(arg, py_avro_schema._typing.DecimalMeta))
            except ValueError:  # not enough/too many values to unpack
                raise TypeError(f"{py_type} is not annotated with a single 'py_avro_schema.DecimalMeta' object")
            return meta
        elif origin is decimal.Decimal:
            # Deprecated pas.DecimalType[4, 2]
            if cls._validate_meta_tuple(args):
                return py_avro_schema._typing.DecimalMeta(precision=args[0], scale=args[1])
            else:
                raise TypeError(f"{py_type} is not annotated with a tuple of integers (precision, scale)")
        else:
            # Anything else is not a supported decimal type
            raise TypeError(f"{py_type} is not a decimal type")

    @staticmethod
    def _validate_meta_tuple(tuple_: Tuple) -> bool:
        """Checks whether a given tuple is a tuple of (precision, scale)"""
        return len(tuple_) == 2 and all(isinstance(item, int) for item in tuple_)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        meta = self._decimal_meta(self.py_type)
        data_ = {
            "type": "bytes",
            "logicalType": "decimal",
            "precision": meta.precision,
        }
        if meta.scale is not None:  # Avro spec: scale is optional, equals to zero when omitted
            data_["scale"] = meta.scale
        return data_

    def make_default(self, py_default: decimal.Decimal) -> str:
        """Return an Avro schema compliant default value for a given Python value"""
        meta = self._decimal_meta(self.py_type)
        scale = meta.scale or 0  # Scale is optional in Avro and should be interpreted as zero when omitted
        sign, digits, exp = py_default.as_tuple()
        assert isinstance(exp, int)  # for mypy
        if len(digits) > meta.precision:
            raise ValueError(
                f"Default value {py_default} has precision {len(digits)} which is greater than the schema's precision "
                f"{meta.precision}"
            )
        delta = exp + scale
        if delta < 0:
            raise ValueError(
                f"Default value {py_default} has scale {-exp} which is greater than the schema's scale {scale}"
            )

        unscaled_datum = 0
        for digit in digits:
            unscaled_datum = (unscaled_datum * 10) + digit
        unscaled_datum = 10**delta * unscaled_datum
        bytes_req = (unscaled_datum.bit_length() + 8) // 8
        if sign:
            unscaled_datum = -unscaled_datum
        return r"\u" + unscaled_datum.to_bytes(bytes_req, byteorder="big", signed=True).hex()


# Recursive schemas ----------------------------------------------------------------------------------------------------


class SequenceSchema(Schema):
    """An Avro array schema for a given Python sequence"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        origin = get_origin(py_type)
        return _is_class(origin, collections.abc.Sequence)

    def __init__(
        self,
        py_type: Type[collections.abc.MutableSequence],
        namespace: Optional[str] = None,
        options: Option = Option(0),
    ):
        """
        An Avro array schema for a given Python sequence

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        args = get_args(py_type)  # TODO: validate if args has exactly 1 item?
        self.items_schema = _schema_obj(args[0], namespace=namespace, options=options)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        return {
            "type": "array",
            "items": self.items_schema.data(names=names),
        }


class DictSchema(Schema):
    """An Avro map schema for a given Python mapping"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        origin = get_origin(py_type)
        args = get_args(py_type)
        # TODO: should we return false if args does not have 2 items?
        return _is_class(origin, collections.abc.Mapping) and args[1] != Any  # dict values must be strongly typed

    def __init__(
        self,
        py_type: Type[collections.abc.MutableMapping],
        namespace: Optional[str] = None,
        options: Option = Option(0),
    ):
        """
        An Avro map schema for a given Python mapping

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        args = get_args(py_type)
        if args[0] != str:
            raise TypeError(f"Cannot generate Avro mapping schema for Python dictionary {py_type} with non-string keys")
        self.values_schema = _schema_obj(args[1], namespace=namespace, options=options)

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        return {
            "type": "map",
            "values": self.values_schema.data(names=names),
        }


class UnionSchema(Schema):
    """An Avro union schema for a given Python union type"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        origin = get_origin(py_type)

        # Support for `X | Y` syntax available in Python 3.10+
        # equivalent to `typing.Union[X, Y]`
        if getattr(types, "UnionType", None):
            return origin == Union or origin == types.UnionType  # noqa: E721
        return origin == Union

    def __init__(self, py_type: Type[Union[Any]], namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro union schema for a given Python union type

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        args = get_args(py_type)
        self.item_schemas = [_schema_obj(arg, namespace=namespace, options=options) for arg in args]

    def data(self, names: NamesType) -> JSONArray:
        """Return the schema data"""
        return [schema.data(names=names) for schema in self.item_schemas]

    def sort_item_schemas(self, default_value: Any) -> None:
        """Re-order the union's schemas such that the first item corresponds with a record field's default value"""
        default_index = -1
        for i, item_schema in enumerate(self.item_schemas):
            try:
                typeguard.check_type(default_value, item_schema.py_type)
                default_index = i
                break
            except typeguard.TypeCheckError:
                continue
        if default_index > 0:
            default_item_schema = self.item_schemas.pop(default_index)
            self.item_schemas.insert(0, default_item_schema)


# Named schemas --------------------------------------------------------------------------------------------------------


class NamedSchema(Schema):
    """A named Avro schema base class"""

    def __init__(self, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        A named Avro schema base class

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        self.name = py_type.__name__

    def __str__(self):
        """Human rendering of the schema"""
        return self.fullname

    @property
    def fullname(self):
        """The schema's full name including the namespace if set"""
        if self.namespace:
            return ".".join((self.namespace, self.name))
        else:
            return self.name

    def data(self, names: NamesType) -> JSONType:
        """Return the schema data"""
        if self.fullname in names:
            return self.fullname
        else:
            names.append(self.fullname)
            return self.data_before_deduplication(names=names)

    @abc.abstractmethod
    def data_before_deduplication(self, names: NamesType) -> JSONObj:
        """Return the schema data"""


class EnumSchema(NamedSchema):
    """An Avro enum schema for a Python enum with string values"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        return _is_class(py_type, enum.Enum)

    def __init__(self, py_type: Type[enum.Enum], namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro enum schema for a Python enum with string values

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        self.symbols = [member.value for member in py_type]
        symbol_types = {type(symbol) for symbol in self.symbols}
        if symbol_types != {str}:
            raise TypeError(f"Avro enum schema members must be strings. {py_type} uses {symbol_types} values.")

    def data_before_deduplication(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        enum_schema = {
            "type": "enum",
            "name": self.name,
            "symbols": self.symbols,
            # This is the default for the enum, not the default value for a record field using the enum type! See Avro
            # schema specification for use. For now, we force the default value to be the first symbol. This means that
            # if the writer schema has an additional member that the reader schema does NOT have, the reader will simply
            # and silently assume the default specified here. Now that may not always be what we want, but standard lib
            # Python enums don't really have a way to specify this.
            "default": self.symbols[0],
        }
        if self.namespace is not None:
            enum_schema["namespace"] = self.namespace
        if Option.NO_DOC not in self.options:
            doc = _doc_for_class(self.py_type)
            if doc:
                enum_schema["doc"] = doc
        return enum_schema


class RecordSchema(NamedSchema):
    """An Avro record schema base class"""

    def __init__(self, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro record schema base class

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        self.record_fields: collections.abc.Sequence[RecordField] = []

    def data_before_deduplication(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        record_schema = {
            "type": "record",
            "name": self.name,
            "fields": [field.data(names=names) for field in self.record_fields],
        }
        if self.namespace is not None:
            record_schema["namespace"] = self.namespace
        if Option.NO_DOC not in self.options:
            doc = _doc_for_class(self.py_type)
            if doc:
                record_schema["doc"] = doc
        return record_schema


class RecordField:
    """An Avro record field"""

    def __init__(
        self,
        py_type: Type,
        name: str,
        namespace: Optional[str],
        default: Any = dataclasses.MISSING,
        docs: str = "",
        options: Option = Option(0),
    ):
        """
        An Avro record field

        :param py_type:   The Python class or type
        :param name:      Field name
        :param namespace: Avro schema namespace
        :param default:   Field default value
        :param docs:      Field documentation or description
        :param options:   Schema generation options
        """
        self.py_type = py_type
        self.name = name
        self._namespace = namespace
        self.default = default
        self.docs = docs
        self.options = options
        self.schema = _schema_obj(self.py_type, namespace=self._namespace, options=options)

        if self.default != dataclasses.MISSING:
            if isinstance(self.schema, UnionSchema):
                self.schema.sort_item_schemas(self.default)
            typeguard.check_type(self.default, self.py_type)
        else:
            if Option.DEFAULTS_MANDATORY in self.options:
                raise TypeError(f"Default value for field {self} is missing")

    def __str__(self):
        """Human representation of the field"""
        return self.name

    def data(self, names: NamesType) -> JSONObj:
        """Return the schema data"""
        field_data = {
            "name": self.name,
            "type": self.schema.data(names=names),
        }
        if self.default != dataclasses.MISSING:
            field_data["default"] = self.schema.make_default(self.default)
        if self.docs and Option.NO_DOC not in self.options:
            field_data["doc"] = self.docs
        return field_data


class DataclassSchema(RecordSchema):
    """An Avro record schema for a given Python dataclass"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        return dataclasses.is_dataclass(py_type)

    def __init__(self, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro record schema for a given Python dataclass

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        self.py_fields = dataclasses.fields(py_type)
        self.record_fields = [self._record_field(field) for field in self.py_fields]

    def _record_field(self, py_field: dataclasses.Field) -> RecordField:
        """Return an Avro record field object for a given dataclass field"""
        default = py_field.default
        if callable(py_field.default_factory):  # type: ignore
            default = py_field.default_factory()  # type: ignore
        field_obj = RecordField(
            py_type=py_field.type,
            name=py_field.name,
            namespace=self.namespace_override,
            default=default,
            options=self.options,
        )
        return field_obj


class PydanticSchema(RecordSchema):
    """An Avro record schema for a given Pydantic model class"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        return hasattr(py_type, "__fields__")

    def __init__(self, py_type: Type[pydantic.BaseModel], namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro record schema for a given Pydantic model class

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        self.py_fields = py_type.model_fields
        self.record_fields = [self._record_field(name, field) for name, field in self.py_fields.items()]

    def _record_field(self, name: str, py_field: pydantic.fields.FieldInfo) -> RecordField:
        """Return an Avro record field object for a given Pydantic model field"""
        default = dataclasses.MISSING if py_field.is_required() else py_field.get_default(call_default_factory=True)
        py_type = self._annotation(name)
        record_name = py_field.alias if Option.USE_FIELD_ALIAS in self.options and py_field.alias else name
        field_obj = RecordField(
            py_type=py_type,
            name=record_name,
            namespace=self.namespace_override,
            default=default,
            docs=py_field.description or "",
            options=self.options,
        )
        return field_obj

    def _annotation(self, field_name: str) -> Type:
        """
        Fetch the raw annotation for a given field name

        Pydantic "unpacks" annotated and forward ref types in their FieldInfo API. We need to access to full, raw
        annotated type hints instead.
        """
        for class_ in self.py_type.mro():
            if class_.__annotations__.get(field_name):
                return class_.__annotations__[field_name]
        raise ValueError(f"{field_name} is not a field of {self.py_type}")  # Should never happen

    def make_default(self, py_default: pydantic.BaseModel) -> Any:
        """Naive implementation"""
        # A more correct implementation would recursively serialize all Pydantic fields as per Avro schema
        # specification. Probably should be implemented using the `make_default` methods.
        return dict(py_default)


class PlainClassSchema(RecordSchema):
    """An Avro record schema for a plain Python class with typed constructor method arguments"""

    @classmethod
    def handles_type(cls, py_type: Type) -> bool:
        """Whether this schema class can represent a given Python class"""
        py_type = _type_from_annotated(py_type)
        return (
            # Dataclasses are handled above
            not dataclasses.is_dataclass(py_type)
            # Pydantic models are handled above
            and not hasattr(py_type, "__fields__")
            # If we are subclassing a string, used the "named string" approach
            and (inspect.isclass(py_type) and not issubclass(py_type, str))
            # Any other class with __init__ with typed args
            and bool(get_type_hints(py_type.__init__))
        )

    def __init__(self, py_type: Type, namespace: Optional[str] = None, options: Option = Option(0)):
        """
        An Avro record schema for a plain Python class with typed constructor method arguments

        :param py_type:   The Python class to generate a schema for.
        :param namespace: The Avro namespace to add to schemas.
        :param options:   Schema generation options.
        """
        super().__init__(py_type, namespace=namespace, options=options)
        py_type = _type_from_annotated(py_type)
        # Extracting arguments from __init__, dropping first argument `self`.
        self.py_fields = list(inspect.signature(py_type.__init__).parameters.values())[1:]
        self.record_fields = [self._record_field(field) for field in self.py_fields]

    def _record_field(self, py_field: inspect.Parameter) -> RecordField:
        """Return an Avro record field object for a given Python instance attribute"""
        default = py_field.default if py_field.default != inspect.Parameter.empty else dataclasses.MISSING
        field_obj = RecordField(
            py_type=py_field.annotation,
            name=py_field.name,
            namespace=self.namespace_override,
            default=default,
            options=self.options,
        )
        return field_obj


def _doc_for_class(py_type: Type) -> str:
    """Return the first line of the docstring for a given class, if any"""
    doc = inspect.getdoc(py_type)
    if doc:
        # Take the first sentence
        doc = doc.split("\n\n", 1)[0].replace("\n", " ").replace("  ", " ").strip()
        return doc
    else:
        return ""


def _is_dict_str_any(py_type: Type) -> bool:
    """Return whether a given type is ``Dict[str, Any]``"""
    origin = get_origin(py_type)
    return inspect.isclass(origin) and issubclass(origin, dict) and get_args(py_type) == (str, Any)


def _is_list_dict_str_any(py_type: Type) -> bool:
    """Return whether a given type is ``List[Dict[str, Any]]``"""
    origin = get_origin(py_type)
    args = get_args(py_type)
    if args:
        return inspect.isclass(origin) and issubclass(origin, list) and _is_dict_str_any(args[0])
    else:
        return False


def _is_class(py_type: Any, of_types: Union[Type, Tuple[Type, ...]], include_subclasses: bool = True) -> bool:
    """Return whether the given type is a (sub) class of a type or types"""
    py_type = _type_from_annotated(py_type)
    if include_subclasses:
        return inspect.isclass(py_type) and issubclass(py_type, of_types)
    else:
        if isinstance(of_types, tuple):
            return py_type in of_types
        else:
            return py_type == of_types


def _type_from_annotated(py_type: Type) -> Type:
    """
    Return the "principal" type if the given type is annotated like this ``Annotated[{principal_type}, ...]``

    If it's not annotated, just return the type itself
    """
    args = get_args(py_type)
    if get_origin(py_type) == Annotated and args:
        return args[0]
    else:
        return py_type
