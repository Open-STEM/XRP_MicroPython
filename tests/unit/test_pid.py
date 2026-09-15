"""
Unit tests for PID controller logic.
"""
import time
import pytest
from XRPLib.pid import PID


class TestPIDBasic:
    def test_proportional_only(self):
        pid = PID(kp=1.0, ki=0, kd=0, min_output=0, max_output=10)
        output = pid.update(5.0)
        assert output == pytest.approx(5.0, abs=0.1)

    def test_proportional_negative_error(self):
        pid = PID(kp=1.0, ki=0, kd=0, min_output=0, max_output=10)
        output = pid.update(-3.0)
        assert output == pytest.approx(-3.0, abs=0.1)

    def test_proportional_scaling(self):
        pid = PID(kp=0.5, ki=0, kd=0, min_output=0, max_output=10)
        output = pid.update(4.0)
        assert output == pytest.approx(2.0, abs=0.1)

    def test_zero_error(self):
        pid = PID(kp=1.0, ki=0, kd=0, min_output=0, max_output=10)
        # With min_output=0, zero error should give zero-ish output
        output = pid.update(0.0)
        assert abs(output) < 0.01


class TestPIDOutputBounds:
    def test_max_output_clamping(self):
        pid = PID(kp=10.0, ki=0, kd=0, min_output=0, max_output=1.0)
        output = pid.update(5.0)
        assert output == pytest.approx(1.0)

    def test_max_output_clamping_negative(self):
        pid = PID(kp=10.0, ki=0, kd=0, min_output=0, max_output=1.0)
        output = pid.update(-5.0)
        assert output == pytest.approx(-1.0)

    def test_min_output_positive(self):
        pid = PID(kp=0.001, ki=0, kd=0, min_output=0.3, max_output=1.0)
        output = pid.update(1.0)
        # Small kp * error = 0.001, but min_output forces it to 0.3
        assert output >= 0.3

    def test_min_output_negative(self):
        pid = PID(kp=0.001, ki=0, kd=0, min_output=0.3, max_output=1.0)
        output = pid.update(-1.0)
        assert output <= -0.3


class TestPIDIntegral:
    def test_integral_accumulates(self):
        pid = PID(kp=0, ki=1.0, kd=0, min_output=0, max_output=100)
        # Call update multiple times with constant error
        for _ in range(10):
            output = pid.update(1.0)
            time.sleep(0.01)
        # Integral should have accumulated, output should be positive and growing
        assert output > 0

    def test_integral_windup_cap(self):
        pid = PID(kp=0, ki=1.0, kd=0, min_output=0, max_output=100, max_integral=5.0)
        # Push integral hard
        for _ in range(100):
            pid.update(10.0)
            time.sleep(0.01)
        # Integral term should be capped at max_integral * ki = 5.0
        assert pid.prev_integral <= 5.0
        assert pid.prev_integral >= -5.0

    def test_integral_negative(self):
        pid = PID(kp=0, ki=1.0, kd=0, min_output=0, max_output=100, max_integral=50)
        for _ in range(10):
            pid.update(-1.0)
            time.sleep(0.01)
        assert pid.prev_integral < 0


class TestPIDDerivative:
    def test_derivative_responds_to_change(self):
        pid = PID(kp=0, ki=0, kd=1.0, min_output=0, max_output=100)
        pid.update(0.0)
        time.sleep(0.01)
        output = pid.update(10.0)
        # Error jumped from 0 to 10, derivative should be large positive
        assert output > 0


class TestPIDRateLimiting:
    def test_max_derivative_limits_output_change(self):
        pid = PID(kp=10.0, ki=0, kd=0, min_output=0, max_output=100, max_derivative=1.0)
        pid.update(0.0)
        time.sleep(0.05)
        output = pid.update(100.0)
        # Without rate limiting, output would be 100. With max_derivative=1.0,
        # it should be limited to prev_output + max_derivative * dt
        assert output < 10.0


class TestPIDTolerance:
    def test_not_done_initially(self):
        pid = PID(tolerance=0.5, tolerance_count=3)
        pid.update(10.0)
        assert not pid.is_done()

    def test_done_after_tolerance_count(self):
        pid = PID(kp=1.0, ki=0, kd=0, min_output=0, max_output=1.0,
                  tolerance=1.0, tolerance_count=3)
        # Feed small errors within tolerance (sleep to avoid zero timestep)
        for _ in range(5):
            pid.update(0.1)
            time.sleep(0.002)
        assert pid.is_done()

    def test_tolerance_resets_on_large_error(self):
        pid = PID(tolerance=0.5, tolerance_count=3)
        pid.update(0.1); time.sleep(0.002)
        pid.update(0.1); time.sleep(0.002)
        pid.update(5.0); time.sleep(0.002)  # outside tolerance — resets counter
        pid.update(0.1); time.sleep(0.002)
        pid.update(0.1)
        assert not pid.is_done()  # only 2 consecutive, need 3


class TestPIDClearHistory:
    def test_clear_resets_state(self):
        pid = PID(kp=1.0, ki=1.0, kd=1.0, min_output=0, max_output=100)
        for _ in range(5):
            pid.update(10.0)
            time.sleep(0.01)
        pid.clear_history()
        assert pid.prev_error == 0
        assert pid.prev_integral == 0
        assert pid.prev_output == 0
        assert pid.prev_time is None
        assert pid.times == 0
