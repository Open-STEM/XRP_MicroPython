"""
Unit tests for SinglePWMMotor and DualPWMMotor.
"""
import pytest
from XRPLib.motor import SinglePWMMotor, DualPWMMotor


class TestSinglePWMMotor:
    def test_effort_zero(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(0)
        assert m._in2SpeedPin.duty_u16() == 0

    def test_effort_positive(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(0.5)
        expected = int(0.5 * 65534)
        assert m._in2SpeedPin.duty_u16() == expected
        assert m._in1DirPin._value == 0  # forward direction

    def test_effort_negative(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(-0.5)
        expected = int(0.5 * 65534)
        assert m._in2SpeedPin.duty_u16() == expected
        assert m._in1DirPin._value == 1  # reverse direction

    def test_effort_clamped_above_one(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(1.5)
        assert m._in2SpeedPin.duty_u16() == 65534  # clamped to 1.0

    def test_effort_clamped_below_neg_one(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(-1.5)
        assert m._in2SpeedPin.duty_u16() == 65534  # clamped to 1.0 magnitude

    def test_flip_dir(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2", flip_dir=True)
        m.set_effort(0.5)
        assert m._in1DirPin._value == 1  # inverted: forward becomes 1

    def test_brake(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.brake()
        assert m._in2SpeedPin.duty_u16() == 65535

    def test_coast(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        m.set_effort(0.5)
        m.coast()
        assert m._in2SpeedPin.duty_u16() == 0

    def test_pwm_frequency(self):
        m = SinglePWMMotor("MOTOR_L_IN_1", "MOTOR_L_IN_2")
        assert m._in2SpeedPin.freq() == 50


class TestDualPWMMotor:
    def test_effort_positive_no_flip(self):
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2")
        m.set_effort(0.5)
        # effort > 0, flip_dir=False: in1Pwm = False ^ False = False
        # So in2 gets the duty, in1 is 0
        assert m._in2BackwardPin.duty_u16() == int(0.5 * 65535)
        assert m._in1ForwardPin.duty_u16() == 0

    def test_effort_negative_no_flip(self):
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2")
        m.set_effort(-0.5)
        # effort < 0, flip_dir=False: in1Pwm = True ^ False = True
        assert m._in1ForwardPin.duty_u16() == int(0.5 * 65535)
        assert m._in2BackwardPin.duty_u16() == 0

    def test_flip_dir(self):
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2", flip_dir=True)
        m.set_effort(0.5)
        # effort > 0, flip_dir=True: in1Pwm = False ^ True = True
        assert m._in1ForwardPin.duty_u16() == int(0.5 * 65535)
        assert m._in2BackwardPin.duty_u16() == 0

    def test_brake(self):
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2")
        m.brake()
        assert m._in1ForwardPin.duty_u16() == 65535
        assert m._in2BackwardPin.duty_u16() == 65535

    def test_coast(self):
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2")
        m.set_effort(0.5)
        m.coast()
        assert m._in1ForwardPin.duty_u16() == 0
        assert m._in2BackwardPin.duty_u16() == 0

    def test_no_input_clamping_bug(self):
        """Documents the current bug: DualPWMMotor doesn't clamp effort > 1.0"""
        m = DualPWMMotor("MOTOR_R_IN_1", "MOTOR_R_IN_2")
        m.set_effort(1.5)
        # This will produce duty > 65535, which is the bug documented in the code review
        duty = m._in2BackwardPin.duty_u16()
        assert duty > 65535  # confirms the bug exists
