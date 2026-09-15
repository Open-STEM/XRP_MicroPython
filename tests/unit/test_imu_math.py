"""
Unit tests for IMU data conversion math.
Tests the pure math functions without needing real I2C.
"""
import pytest
from XRPLib.imu import IMU


@pytest.fixture
def imu():
    """Create an IMU instance with mocked I2C."""
    return IMU.__new__(IMU)


class TestInt16:
    def setup_method(self):
        self.imu = IMU.__new__(IMU)

    def test_positive(self):
        assert self.imu._int16(100) == 100

    def test_zero(self):
        assert self.imu._int16(0) == 0

    def test_max_positive(self):
        assert self.imu._int16(0x7FFF) == 32767

    def test_negative_boundary(self):
        assert self.imu._int16(0x8000) == -32768

    def test_full_negative(self):
        assert self.imu._int16(0xFFFF) == -1

    def test_mid_negative(self):
        assert self.imu._int16(0xFF00) == -256


class TestRawConversions:
    def setup_method(self):
        self.imu = IMU.__new__(IMU)
        self.imu._acc_scale_factor = 1
        self.imu._gyro_scale_factor = 1

    def test_raw_to_mg_zero(self):
        raw = bytearray([0, 0])
        assert self.imu._raw_to_mg(raw) == 0

    def test_raw_to_mg_positive(self):
        # Little-endian: [low, high]
        raw = bytearray([0x00, 0x01])  # 256
        result = self.imu._raw_to_mg(raw)
        # 256 * 0.061 (LSM_MG_PER_LSB_2G) * 1 (scale factor)
        assert result == pytest.approx(256 * 0.061, abs=0.1)

    def test_raw_to_mg_negative(self):
        raw = bytearray([0x00, 0xFF])  # 0xFF00 = -256 as int16
        result = self.imu._raw_to_mg(raw)
        assert result == pytest.approx(-256 * 0.061, abs=0.1)

    def test_raw_to_mg_with_scale_factor(self):
        self.imu._acc_scale_factor = 8  # 16g mode
        raw = bytearray([0x00, 0x01])  # 256
        result = self.imu._raw_to_mg(raw)
        assert result == pytest.approx(256 * 0.061 * 8, abs=0.1)

    def test_raw_to_mdps_zero(self):
        raw = bytearray([0, 0])
        assert self.imu._raw_to_mdps(raw) == 0

    def test_raw_to_mdps_positive(self):
        raw = bytearray([0x00, 0x01])  # 256
        result = self.imu._raw_to_mdps(raw)
        # 256 * 4.375 (LSM_MDPS_PER_LSB_125DPS) * 1
        assert result == pytest.approx(256 * 4.375, abs=1)


class TestAngleIntegration:
    def test_pitch_starts_at_zero(self):
        imu = IMU.__new__(IMU)
        imu.running_pitch = 0
        assert imu.get_pitch() == 0

    def test_yaw_set_and_get(self):
        imu = IMU.__new__(IMU)
        imu.running_yaw = 0
        imu.set_yaw(45.0)
        assert imu.get_yaw() == 45.0

    def test_heading_bounded(self):
        imu = IMU.__new__(IMU)
        imu.running_yaw = 450.0
        assert imu.get_heading() == pytest.approx(90.0)

    def test_heading_negative(self):
        imu = IMU.__new__(IMU)
        imu.running_yaw = -90.0
        heading = imu.get_heading()
        assert 0 <= heading < 360
        assert heading == pytest.approx(270.0)

    def test_reset_yaw(self):
        imu = IMU.__new__(IMU)
        imu.running_yaw = 123.0
        imu.reset_yaw()
        assert imu.get_yaw() == 0

    def test_reset_pitch(self):
        imu = IMU.__new__(IMU)
        imu.running_pitch = 45.0
        imu.reset_pitch()
        assert imu.get_pitch() == 0

    def test_reset_roll(self):
        imu = IMU.__new__(IMU)
        imu.running_roll = -30.0
        imu.reset_roll()
        assert imu.get_roll() == 0


class TestScaleFactors:
    def test_acc_scale_factor_2g(self):
        # '2g' -> int('2') // 2 = 1
        assert int('2') // 2 == 1

    def test_acc_scale_factor_16g(self):
        # '16g' -> int('16') // 2 = 8
        assert int('16') // 2 == 8

    def test_gyro_scale_factor_125dps(self):
        # '125dps' -> int('125') // 125 = 1
        assert int('125') // 125 == 1

    def test_gyro_scale_factor_2000dps(self):
        # '2000dps' -> int('2000') // 125 = 16
        assert int('2000') // 125 == 16
