"""
Hardware integration test for rangefinder.
Setup: Place a flat surface (wall/book) at a known distance from the sensor.
"""
from XRPLib.rangefinder import Rangefinder
from XRPLib.board import Board
import time

rf = Rangefinder.get_default_rangefinder()
board = Board.get_default_board()

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


def test_first_reading():
    """First call to distance() should return a valid number."""
    d = rf.distance()
    check(f"First reading is numeric: {d:.1f}cm", isinstance(d, (int, float)))


def test_reasonable_range():
    """Distance should be within sensor range (2-400cm) or MAX_VALUE."""
    d = rf.distance()
    check(f"Reading in range: {d:.1f}cm",
          (2 < d < 400) or d == rf.MAX_VALUE)


def test_stability():
    """10 readings at a fixed distance should have low variance."""
    time.sleep(0.5)  # Let a few readings accumulate
    readings = []
    for _ in range(10):
        readings.append(rf.distance())
        time.sleep(0.1)
    valid = [r for r in readings if r != rf.MAX_VALUE]
    if len(valid) >= 5:
        avg = sum(valid) / len(valid)
        max_dev = max(abs(r - avg) for r in valid)
        check(f"Stability: avg={avg:.1f}cm, max_deviation={max_dev:.1f}cm",
              max_dev < 3.0)
    else:
        check("Stability: not enough valid readings", False)


def test_non_blocking_speed():
    """100 calls to distance() should complete quickly (non-blocking)."""
    start = time.ticks_ms()
    for _ in range(100):
        rf.distance()
    elapsed = time.ticks_diff(time.ticks_ms(), start)
    check(f"100 reads in {elapsed}ms (expect < 200ms)", elapsed < 200)


print("=" * 40)
print("RANGEFINDER HARDWARE TESTS")
print("Point sensor at a surface ~20cm away.")
print("Press button to start.")
print("=" * 40)
board.wait_for_button()

test_first_reading()
test_reasonable_range()
test_stability()
test_non_blocking_speed()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
