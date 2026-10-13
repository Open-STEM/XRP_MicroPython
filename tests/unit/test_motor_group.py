"""
Unit tests for MotorGroup aggregation logic.
"""
import pytest
from unittest.mock import MagicMock
from XRPLib.motor_group import MotorGroup


def _make_mock_motor(position=0.0, position_counts=0, speed=0.0):
    m = MagicMock()
    m.get_position.return_value = position
    m.get_position_counts.return_value = position_counts
    m.get_speed.return_value = speed
    return m


class TestMotorGroupAverages:
    def test_average_position(self):
        m1 = _make_mock_motor(position=1.0)
        m2 = _make_mock_motor(position=3.0)
        g = MotorGroup(m1, m2)
        assert g.get_position() == pytest.approx(2.0)

    def test_average_position_counts(self):
        m1 = _make_mock_motor(position_counts=100)
        m2 = _make_mock_motor(position_counts=200)
        g = MotorGroup(m1, m2)
        assert g.get_position_counts() == 150

    def test_average_speed(self):
        m1 = _make_mock_motor(speed=60.0)
        m2 = _make_mock_motor(speed=40.0)
        g = MotorGroup(m1, m2)
        assert g.get_speed() == pytest.approx(50.0)

    def test_single_motor(self):
        m1 = _make_mock_motor(position=5.0)
        g = MotorGroup(m1)
        assert g.get_position() == pytest.approx(5.0)


class TestMotorGroupDelegation:
    def test_set_effort_all(self):
        m1 = _make_mock_motor()
        m2 = _make_mock_motor()
        g = MotorGroup(m1, m2)
        g.set_effort(0.7)
        m1.set_effort.assert_called_with(0.7)
        m2.set_effort.assert_called_with(0.7)

    def test_reset_encoder_all(self):
        m1 = _make_mock_motor()
        m2 = _make_mock_motor()
        g = MotorGroup(m1, m2)
        g.reset_encoder_position()
        m1.reset_encoder_position.assert_called_once()
        m2.reset_encoder_position.assert_called_once()

    def test_set_speed_all(self):
        m1 = _make_mock_motor()
        m2 = _make_mock_motor()
        g = MotorGroup(m1, m2)
        g.set_speed(60.0)
        m1.set_speed.assert_called_with(60.0)
        m2.set_speed.assert_called_with(60.0)


class TestMotorGroupAddRemove:
    def test_add_motor(self):
        m1 = _make_mock_motor()
        g = MotorGroup(m1)
        assert len(g.motors) == 1
        m2 = _make_mock_motor()
        g.add_motor(m2)
        assert len(g.motors) == 2

    def test_remove_motor(self):
        m1 = _make_mock_motor()
        m2 = _make_mock_motor()
        g = MotorGroup(m1, m2)
        g.remove_motor(m1)
        assert len(g.motors) == 1
        assert g.motors[0] is m2

    def test_remove_nonexistent_motor(self):
        m1 = _make_mock_motor()
        g = MotorGroup(m1)
        m2 = _make_mock_motor()
        # Should not raise, just print
        g.remove_motor(m2)
        assert len(g.motors) == 1
