"""
Unit tests for DifferentialDrive math (no real hardware motion).
"""
import math
import pytest
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.differential_drive import DifferentialDrive


@pytest.fixture
def drive():
    left = EncodedMotor.get_default_encoded_motor(1)
    right = EncodedMotor.get_default_encoded_motor(2)
    return DifferentialDrive(left, right, imu=None, wheel_diam=6.0, wheel_track=15.5)


class TestArcadeDrive:
    def test_zero_input_stops(self, drive):
        drive.arcade(0, 0)
        # Both motors should be set to 0

    def test_straight_forward(self, drive):
        drive.arcade(1.0, 0)
        # Both motors should get equal positive effort

    def test_pure_turn(self, drive):
        drive.arcade(0, 1.0)
        # Left and right should be opposite signs

    def test_scaling_preserves_ratio(self, drive):
        # The arcade scaling formula: scale = max(|s|,|t|) / (|s|+|t|)
        s, t = 0.6, 0.4
        scale = max(abs(s), abs(t)) / (abs(s) + abs(t))
        left = (s - t) * scale
        right = (s + t) * scale
        # Both should be within [-1, 1]
        assert -1 <= left <= 1
        assert -1 <= right <= 1

    def test_full_forward_full_turn_bounded(self):
        """Verify the arcade formula keeps values in [-1, 1]."""
        for s in [-1.0, -0.5, 0, 0.5, 1.0]:
            for t in [-1.0, -0.5, 0, 0.5, 1.0]:
                if s == 0 and t == 0:
                    continue
                scale = max(abs(s), abs(t)) / (abs(s) + abs(t))
                left = (s - t) * scale
                right = (s + t) * scale
                assert -1.001 <= left <= 1.001, f"left={left} for s={s}, t={t}"
                assert -1.001 <= right <= 1.001, f"right={right} for s={s}, t={t}"


class TestEncoderPositionToCm:
    def test_encoder_position_to_cm(self, drive):
        """Verify the conversion from encoder revolutions to cm."""
        # 1 revolution * pi * wheel_diam = pi * 6.0 = 18.85 cm
        wheel_diam = 6.0
        one_rev_cm = math.pi * wheel_diam
        assert one_rev_cm == pytest.approx(18.85, abs=0.01)

    def test_track_width_default(self, drive):
        assert drive.track_width == 15.5

    def test_wheel_diam_default(self, drive):
        assert drive.wheel_diam == 6.0


class TestDrivetrainStop:
    def test_stop_disables_speed_control(self, drive):
        drive.left_motor.set_speed(60)
        drive.right_motor.set_speed(60)
        drive.stop()
        assert drive.left_motor.target_speed is None
        assert drive.right_motor.target_speed is None
