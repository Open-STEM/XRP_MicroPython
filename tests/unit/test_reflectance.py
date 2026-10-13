"""
Unit tests for Reflectance sensor normalization.
"""
import pytest
from XRPLib.reflectance import Reflectance


class TestReflectance:
    def test_white_surface_low_value(self):
        r = Reflectance()
        r._leftReflectance._set_value(0)
        assert r.get_left() == pytest.approx(0.0)

    def test_dark_surface_high_value(self):
        r = Reflectance()
        r._leftReflectance._set_value(65535)
        result = r.get_left()
        # Due to MAX_ADC_VALUE being 65536, this is 65535/65536
        assert result == pytest.approx(1.0, abs=0.001)

    def test_mid_value(self):
        r = Reflectance()
        r._rightReflectance._set_value(32768)
        result = r.get_right()
        assert result == pytest.approx(0.5, abs=0.01)

    def test_left_right_independent(self):
        r = Reflectance()
        r._leftReflectance._set_value(10000)
        r._rightReflectance._set_value(50000)
        left = r.get_left()
        right = r.get_right()
        assert left < right

    def test_max_value_not_exactly_one_bug(self):
        """Documents the off-by-one: max read (65535) doesn't produce exactly 1.0."""
        r = Reflectance()
        r._leftReflectance._set_value(65535)
        result = r.get_left()
        # This documents the current behavior — not exactly 1.0
        assert result < 1.0
        assert result > 0.999
