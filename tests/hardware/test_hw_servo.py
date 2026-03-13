"""
Hardware integration test for servos.
Setup: Servo attached with visible arm/horn.
Visual verification required.
"""
from XRPLib.servo import Servo
from XRPLib.board import Board
import time

servo = Servo.get_default_servo(1)
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


def test_angle_sweep():
    """Sweep through angles, verify no crash."""
    try:
        servo.set_angle(0)
        time.sleep(0.5)
        servo.set_angle(90)
        time.sleep(0.5)
        servo.set_angle(180)
        time.sleep(0.5)
        servo.set_angle(90)
        time.sleep(0.5)
        check("Angle sweep 0->90->180->90 (visual check)", True)
    except Exception as e:
        check(f"Angle sweep failed: {e}", False)


def test_free():
    """Free should release the servo."""
    try:
        servo.set_angle(90)
        time.sleep(0.5)
        servo.free()
        time.sleep(0.5)
        check("Free releases servo (verify by hand)", True)
    except Exception as e:
        check(f"Free failed: {e}", False)


print("=" * 40)
print("SERVO HARDWARE TESTS")
print("Watch servo arm for movement.")
print("Press button to start.")
print("=" * 40)
board.wait_for_button()

test_angle_sweep()
test_free()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
