"""
Unit tests for Encoder resolution and position math.
"""
import pytest
from XRPLib.encoder import Encoder


class TestEncoderResolution:
    def test_gear_ratio(self):
        expected = (30/14) * (28/16) * (36/9) * (26/8)
        assert Encoder._gear_ratio == pytest.approx(expected)
        assert Encoder._gear_ratio == pytest.approx(48.75)

    def test_resolution(self):
        assert Encoder.resolution == pytest.approx(585.0)

    def test_counts_per_motor_shaft_revolution(self):
        assert Encoder._counts_per_motor_shaft_revolution == 12


class TestEncoderPosition:
    def test_get_position_zero(self):
        enc = Encoder(0, "MOTOR_L_ENCODER_A", "MOTOR_L_ENCODER_B")
        pos = enc.get_position()
        assert pos == 0.0

    def test_get_position_one_revolution(self):
        enc = Encoder(1, "MOTOR_R_ENCODER_A", "MOTOR_R_ENCODER_B")
        enc.sm._set_count(585)
        pos = enc.get_position()
        assert pos == pytest.approx(1.0)

    def test_get_position_counts_negative(self):
        enc = Encoder(2, "MOTOR_3_ENCODER_A", "MOTOR_3_ENCODER_B")
        # Simulate negative count via 2^32 wraparound
        enc.sm._set_count(2**32 - 100)
        counts = enc.get_position_counts()
        assert counts == -100

    def test_reset_encoder_position(self):
        enc = Encoder(3, "MOTOR_4_ENCODER_A", "MOTOR_4_ENCODER_B")
        enc.sm._set_count(1000)
        enc.reset_encoder_position()
        assert enc.get_position_counts() == 0
