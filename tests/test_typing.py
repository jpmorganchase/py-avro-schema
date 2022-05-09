import decimal

import pytest
import typeguard

from py_avro_schema._typing import DecimalType


def test_decimal_type():
    py_type = DecimalType[4, 2]
    assert py_type.__origin__ is decimal.Decimal
    assert py_type.__args__ == (4, 2)


def test_instance_check():
    py_type = DecimalType[4, 2]
    typeguard.check_type("py_type", decimal.Decimal("1.23"), py_type)


def test_zero_precision():
    with pytest.raises(ValueError, match="Precision 0 must be at least 1"):
        DecimalType[0, 2]


def test_negative_scale():
    with pytest.raises(ValueError, match="Scale -2 must be at least 0"):
        DecimalType[4, -2]


def test_zero_scale():
    py_type = DecimalType[4, 0]
    assert py_type.__args__ == (4, 0)


def test_precision_lt_scale():
    with pytest.raises(ValueError, match="Precision 2 must be greater than or equal to scale 4"):
        DecimalType[2, 4]


def test_bad_indexing():
    with pytest.raises(TypeError, match='type of argument "params" must be a tuple; got int instead'):
        DecimalType[4]
