"""
Unit tests for Servo angle-to-duty conversion.
"""
import pytest
from XRPLib.servo import Servo


class TestServo:
    def test_angle_0(self):
        s = Servo("SERVO_1")
        s.set_angle(0)
        # duty_ns = 0 * 10000 + 500000 = 500000
        assert s._servo.duty_ns() == 500000

    def test_angle_90(self):
        s = Servo("SERVO_1")
        s.set_angle(90)
        # duty_ns = 90 * 10000 + 500000 = 1400000
        assert s._servo.duty_ns() == 1400000

    def test_angle_180(self):
        s = Servo("SERVO_1")
        s.set_angle(180)
        # duty_ns = 180 * 10000 + 500000 = 2300000
        assert s._servo.duty_ns() == 2300000

    def test_angle_200_max(self):
        s = Servo("SERVO_1")
        s.set_angle(200)
        # duty_ns = 200 * 10000 + 500000 = 2500000
        assert s._servo.duty_ns() == 2500000

    def test_free(self):
        s = Servo("SERVO_1")
        s.set_angle(90)
        s.free()
        assert s._servo.duty_ns() == 0

    def test_pwm_frequency(self):
        s = Servo("SERVO_1")
        assert s._servo.freq() == 50

    def test_invalid_index_bug(self):
        """Documents the same return-Exception bug as EncodedMotor."""
        result = Servo.get_default_servo(99)
        assert isinstance(result, Exception)
