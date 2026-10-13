"""
Hardware integration test for servos.
Manual mode: Visual verification of servo arm movement.
Test stand: Break-beam sensor verifies servo arm position.
"""
from XRPLib.servo import Servo
from XRPLib.board import Board
from teststand import is_teststand, wait_if_manual, read_servo_beam
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
    """Sweep through angles. Test stand uses break-beam sensor to verify movement."""
    try:
        servo.set_angle(0)
        time.sleep(0.5)
        if is_teststand():
            beam_at_0 = read_servo_beam()
        servo.set_angle(90)
        time.sleep(0.5)
        servo.set_angle(180)
        time.sleep(0.5)
        if is_teststand():
            beam_at_180 = read_servo_beam()
            check("Servo moved (break-beam changed)", beam_at_0 != beam_at_180)
        else:
            check("Angle sweep 0->90->180 (visual check)", True)
        servo.set_angle(90)
        time.sleep(0.5)
    except Exception as e:
        check(f"Angle sweep failed: {e}", False)


def test_free():
    """Free should release the servo."""
    try:
        servo.set_angle(90)
        time.sleep(0.5)
        servo.free()
        time.sleep(0.5)
        if is_teststand():
            # In teststand mode, just verify no crash — full free verification
            # requires spring-loaded lever (Phase 3 enhancement)
            check("Free command executed (no crash)", True)
        else:
            check("Free releases servo (verify by hand)", True)
    except Exception as e:
        check(f"Free failed: {e}", False)


print("=" * 40)
print("SERVO HARDWARE TESTS")
if not is_teststand():
    print("Watch servo arm for movement.")
    print("Press button to start.")
print("=" * 40)
wait_if_manual(board)

test_angle_sweep()
test_free()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
