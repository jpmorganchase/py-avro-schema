"""
Additional type hint classes etc
"""
import decimal
from typing import _GenericAlias  # type: ignore
from typing import Tuple

import typeguard


class DecimalType:
    """
    A decimal type for type annotations including hints for precision and scale

    Usage
    -----

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
