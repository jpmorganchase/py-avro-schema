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
Additional type hint classes etc
"""
import dataclasses
import decimal
from typing import _GenericAlias  # type: ignore
from typing import Optional, Tuple

import typeguard


@dataclasses.dataclass(frozen=True)  # Needs to be hashable to work in unioned types
class DecimalMeta:
    """
    Meta data to annotate a :class:`decimal.Decimal` with precision and scale information

    Example
    -------

    >>> import decimal
    >>> from typing import Annotated
    >>> my_decimal: Annotated[decimal.Decimal, DecimalMeta(precision=4, scale=2)]

    If scale is omitted it defaults to zero as per Avro specification.
    """

    precision: int
    scale: Optional[int] = None

    def __post_init__(self):
        """
        Validate input data

        See: https://avro.apache.org/docs/1.11.1/specification/#decimal
        """
        if self.precision < 1:
            raise ValueError(f"Precision must be at least 1. Given value: {self.precision}")
        if self.scale is not None:
            if self.scale < 0:
                raise ValueError(f"Scale must be positive. Given value: {self.scale}")
            elif self.scale > self.precision:
                raise ValueError(f"Scale must be no more than precision of {self.precision}. Given value: {self.scale}")


class DecimalType:
    """
    A decimal type for type annotations including hints for precision and scale

    **Deprecated**. See :class:`DecimalMeta` instead.

    Example
    -------

    >>> import decimal
    >>> my_decimal: DecimalType[4, 2] = decimal.Decimal("12.34")

    Here, the subscript ``(4, 2)`` refers to the precision and scale of decimal numbers.
    """

    @typeguard.typechecked()
    def __class_getitem__(cls, params: Tuple[int, int]) -> _GenericAlias:
        """Class indexing/subscription using ``DecimalType[precision, scale]"""
        precision, scale = params
        if precision <= 0:
            raise ValueError(f"Precision {precision} must be at least 1")
        if scale < 0:
            raise ValueError(f"Scale {scale} must be at least 0")
        if precision < scale:
            raise ValueError(f"Precision {precision} must be greater than or equal to scale {scale}")
        # This is a little hacky. We use _GenericAlias without using type parameters. We just use integer instances for
        # scale and precision. That appears to work, but may not be a supported use case. For example, we cannot just do
        # ``DecimalType = _GenericAlias(decimal.Decimal, params)`` because that triggers type enforcement on params.
        # Instead we create new custom class with :meth:`__class_getitem__` returning the "generic".
        return _GenericAlias(decimal.Decimal, params)
