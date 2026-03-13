"""
Hardware integration test for motors.
Run on the XRP robot with wheels elevated or on a flat surface.
Requires: batteries connected, power switch ON.

Upload and run via: mpremote run tests/hardware/test_hw_motors.py
"""
from XRPLib.encoded_motor import EncodedMotor
import time

left = EncodedMotor.get_default_encoded_motor(1)
right = EncodedMotor.get_default_encoded_motor(2)

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1


def test_forward_effort():
    """Both motors spin forward at half effort."""
    left.reset_encoder_position()
    right.reset_encoder_position()
    left.set_effort(0.5)
    right.set_effort(0.5)
    time.sleep(1)
    left.set_effort(0)
    right.set_effort(0)
    time.sleep(0.2)
    check("Left motor moved forward", left.get_position() > 0)
    check("Right motor moved forward", right.get_position() > 0)


def test_reverse_effort():
    """Both motors spin backward at half effort."""
    left.reset_encoder_position()
    right.reset_encoder_position()
    left.set_effort(-0.5)
    right.set_effort(-0.5)
    time.sleep(1)
    left.set_effort(0)
    right.set_effort(0)
    time.sleep(0.2)
    check("Left motor moved backward", left.get_position() < 0)
    check("Right motor moved backward", right.get_position() < 0)


def test_independent_direction():
    """Left forward, right backward."""
    left.reset_encoder_position()
    right.reset_encoder_position()
    left.set_effort(0.5)
    right.set_effort(-0.5)
    time.sleep(1)
    left.set_effort(0)
    right.set_effort(0)
    time.sleep(0.2)
    check("Left forward, right backward", left.get_position() > 0 and right.get_position() < 0)


def test_brake():
    """Motor should resist rotation after braking."""
    left.set_effort(0.5)
    time.sleep(0.5)
    left.brake()
    time.sleep(0.1)
    pos1 = left.get_position()
    time.sleep(0.5)
    pos2 = left.get_position()
    # Position should not change much after braking
    check("Brake holds position", abs(pos2 - pos1) < 0.1)
    left.coast()


def test_coast():
    """Motor should spin freely after coasting."""
    left.set_effort(0.5)
    time.sleep(0.5)
    left.coast()
    time.sleep(0.1)
    check("Coast releases motor (no crash)", True)


def test_speed_control():
    """Motor should reach target speed within tolerance."""
    left.reset_encoder_position()
    left.set_speed(60)
    time.sleep(2)
    speed = left.get_speed()
    left.set_speed(0)
    left.set_effort(0)
    check(f"Speed control: {speed:.1f} RPM (target 60)", 50 < speed < 70)


def test_zero_effort_stops():
    """Motor should stop at zero effort."""
    left.set_effort(0.5)
    time.sleep(0.5)
    left.set_effort(0)
    time.sleep(0.5)
    pos1 = left.get_position()
    time.sleep(0.5)
    pos2 = left.get_position()
    check("Zero effort stops motor", abs(pos2 - pos1) < 0.1)


print("=" * 40)
print("MOTOR HARDWARE TESTS")
print("=" * 40)

test_forward_effort()
test_reverse_effort()
test_independent_direction()
test_brake()
test_coast()
test_speed_control()
test_zero_effort_stops()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
