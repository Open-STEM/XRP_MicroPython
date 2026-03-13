"""
Hardware integration test for encoders.
Run on the XRP robot with wheels elevated.
Requires: batteries connected, power switch ON.
"""
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.encoder import Encoder
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


def test_count_direction():
    """Forward rotation should increase counts."""
    left.reset_encoder_position()
    left.set_effort(0.3)
    time.sleep(1)
    left.set_effort(0)
    time.sleep(0.2)
    counts = left.get_position_counts()
    check(f"Forward counts positive: {counts}", counts > 0)


def test_reverse_counts():
    """Backward rotation should decrease counts."""
    left.reset_encoder_position()
    left.set_effort(-0.3)
    time.sleep(1)
    left.set_effort(0)
    time.sleep(0.2)
    counts = left.get_position_counts()
    check(f"Reverse counts negative: {counts}", counts < 0)


def test_reset():
    """Reset should zero the position."""
    left.set_effort(0.3)
    time.sleep(0.5)
    left.set_effort(0)
    time.sleep(0.2)
    left.reset_encoder_position()
    time.sleep(0.1)
    counts = left.get_position_counts()
    check(f"Reset zeroes position: {counts}", abs(counts) < 5)


def test_resolution():
    """One full wheel revolution should be ~585 counts."""
    left.reset_encoder_position()
    # Drive slowly for approximately 1 revolution
    left.set_effort(0.3)
    while abs(left.get_position()) < 1.0:
        time.sleep(0.01)
    left.set_effort(0)
    time.sleep(0.2)
    counts = abs(left.get_position_counts())
    revs = left.get_position()
    check(f"~1 revolution: {revs:.2f} revs, {counts} counts (expect ~585)",
          500 < counts < 700)


def test_stationary_consistency():
    """Multiple reads of stationary wheel should give same value."""
    left.set_effort(0)
    time.sleep(0.5)
    readings = [left.get_position_counts() for _ in range(10)]
    spread = max(readings) - min(readings)
    check(f"Stationary consistency: spread={spread} counts", spread <= 2)


print("=" * 40)
print("ENCODER HARDWARE TESTS")
print("=" * 40)

test_count_direction()
test_reverse_counts()
test_reset()
test_resolution()
test_stationary_consistency()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
