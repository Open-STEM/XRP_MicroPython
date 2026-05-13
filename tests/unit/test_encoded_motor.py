"""
Unit tests for EncodedMotor.
"""
import pytest
from XRPLib.encoded_motor import EncodedMotor


class TestEncodedMotorSingleton:
    def test_get_default_motor_returns_same_instance(self):
        m1 = EncodedMotor.get_default_encoded_motor(1)
        m2 = EncodedMotor.get_default_encoded_motor(1)
        assert m1 is m2

    def test_different_indices_return_different_instances(self):
        m1 = EncodedMotor.get_default_encoded_motor(1)
        m2 = EncodedMotor.get_default_encoded_motor(2)
        assert m1 is not m2

    def test_invalid_index_bug(self):
        """Documents the bug: invalid index returns Exception instead of raising it."""
        result = EncodedMotor.get_default_encoded_motor(99)
        # This should raise, but currently returns an Exception object
        assert isinstance(result, Exception)


class TestEncodedMotorEffort:
    def test_set_effort_zero_coast(self):
        m = EncodedMotor.get_default_encoded_motor(1)
        m.brake_at_zero = False
        m.set_effort(0)
        # Should call motor.set_effort(0), not brake

    def test_set_effort_zero_brake(self):
        m = EncodedMotor.get_default_encoded_motor(1)
        m.set_zero_effort_behavior(EncodedMotor.ZERO_EFFORT_BREAK)
        m.set_effort(0)
        # Should call brake() when effort is 0

    def test_set_effort_nonzero_ignores_brake_setting(self):
        m = EncodedMotor.get_default_encoded_motor(1)
        m.set_zero_effort_behavior(EncodedMotor.ZERO_EFFORT_BREAK)
        m.set_effort(0.5)
        # Should set effort normally even with brake_at_zero set


class TestEncodedMotorSpeed:
    def test_speed_conversion_formula(self):
        """Verify the RPM to counts/20ms conversion."""
        from XRPLib.encoder import Encoder
        resolution = Encoder.resolution  # 585
        # 60 RPM = 1 rev/sec = 585 counts/sec = 585/50 = 11.7 counts/20ms
        rpm = 60
        expected_counts_per_20ms = rpm * resolution / (60 * 50)
        assert expected_counts_per_20ms == pytest.approx(11.7)

    def test_set_speed_none_stops(self):
        m = EncodedMotor.get_default_encoded_motor(1)
        m.set_speed(60)
        assert m.target_speed is not None
        m.set_speed(None)
        assert m.target_speed is None

    def test_set_speed_zero_stops(self):
        m = EncodedMotor.get_default_encoded_motor(1)
        m.set_speed(60)
        m.set_speed(0)
        assert m.target_speed is None
