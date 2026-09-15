"""
Hardware integration test for reflectance sensors.
Manual mode: Have white paper and dark surface available.
Test stand: Sliding plate with white/black halves is actuated automatically.
"""
from XRPLib.reflectance import Reflectance
from XRPLib.board import Board
from teststand import is_teststand, wait_if_manual, move_reflectance_slide
import time

ref = Reflectance.get_default_reflectance()
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


def test_values_in_range():
    """Readings should be between 0 and 1."""
    left = ref.get_left()
    right = ref.get_right()
    check(f"Left in range: {left:.3f}", 0 <= left <= 1)
    check(f"Right in range: {right:.3f}", 0 <= right <= 1)


def test_white_surface():
    """On white paper, readings should be low."""
    if is_teststand():
        move_reflectance_slide("white")
    else:
        print("  Place sensor over WHITE surface, press button...")
        board.wait_for_button()
    time.sleep(0.1)
    left = ref.get_left()
    right = ref.get_right()
    check(f"White left={left:.3f} (expect < 0.4)", left < 0.4)
    check(f"White right={right:.3f} (expect < 0.4)", right < 0.4)


def test_dark_surface():
    """On dark surface, readings should be high."""
    if is_teststand():
        move_reflectance_slide("black")
    else:
        print("  Place sensor over DARK surface, press button...")
        board.wait_for_button()
    time.sleep(0.1)
    left = ref.get_left()
    right = ref.get_right()
    check(f"Dark left={left:.3f} (expect > 0.6)", left > 0.6)
    check(f"Dark right={right:.3f} (expect > 0.6)", right > 0.6)


print("=" * 40)
print("REFLECTANCE HARDWARE TESTS")
print("=" * 40)

test_values_in_range()
test_white_surface()
test_dark_surface()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
