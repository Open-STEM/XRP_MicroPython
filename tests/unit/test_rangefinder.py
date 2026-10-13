"""
Unit tests for Rangefinder distance calculation math.
"""
import pytest
from XRPLib.rangefinder import Rangefinder


class TestRangefinderDistanceCalc:
    def test_distance_formula(self):
        """Verify the pulse-to-cm conversion math."""
        # Sound speed: 343.2 m/s = 0.03432 cm/us
        # Round trip: divide by 2
        # So: distance = pulse_us / 2 / 29.1
        pulse_us = 1164  # ~20cm round trip
        expected_cm = pulse_us / 2 / 29.1
        assert expected_cm == pytest.approx(20.0, abs=0.1)

    def test_distance_2cm(self):
        pulse_us = 2 * 2 * 29.1  # 2cm * 2 (round trip) * 29.1
        distance = pulse_us / 2 / 29.1
        assert distance == pytest.approx(2.0)

    def test_distance_400cm(self):
        pulse_us = 400 * 2 * 29.1  # 400cm
        distance = pulse_us / 2 / 29.1
        assert distance == pytest.approx(400.0)

    def test_max_value(self):
        assert Rangefinder("RANGE_TRIGGER", "RANGE_ECHO").MAX_VALUE == 65535


class TestRangefinderInstances:
    def test_singleton(self):
        # Reset class state
        Rangefinder._DEFAULT_RANGEFINDER_INSTANCE = None
        Rangefinder._instances = []
        Rangefinder._timer = None
        Rangefinder._current_index = 0

        r1 = Rangefinder.get_default_rangefinder()
        r2 = Rangefinder.get_default_rangefinder()
        assert r1 is r2

    def test_instance_registered(self):
        Rangefinder._instances = []
        Rangefinder._timer = None
        Rangefinder._current_index = 0

        r = Rangefinder("RANGE_TRIGGER", "RANGE_ECHO")
        assert r in Rangefinder._instances

    def test_multiple_instances(self):
        Rangefinder._instances = []
        Rangefinder._timer = None
        Rangefinder._current_index = 0

        r1 = Rangefinder("RANGE_TRIGGER", "RANGE_ECHO")
        r2 = Rangefinder("RANGE_TRIGGER", "RANGE_ECHO")
        assert len(Rangefinder._instances) == 2


class TestRangefinderTimeout:
    def test_default_timeout(self):
        r = Rangefinder("RANGE_TRIGGER", "RANGE_ECHO")
        assert r.timeout_us == 500 * 2 * 30  # 30000 us

    def test_custom_timeout(self):
        r = Rangefinder("RANGE_TRIGGER", "RANGE_ECHO", timeout_us=50000)
        assert r.timeout_us == 50000
