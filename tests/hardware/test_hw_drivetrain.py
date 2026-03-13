"""
Hardware integration test for drivetrain.
Run on the XRP robot on a flat, open surface.
Requires: batteries connected, power switch ON, clear space.
"""
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.imu import IMU
from XRPLib.differential_drive import DifferentialDrive
from XRPLib.board import Board
import time

left = EncodedMotor.get_default_encoded_motor(1)
right = EncodedMotor.get_default_encoded_motor(2)
imu = IMU.get_default_imu()
drive = DifferentialDrive.get_default_differential_drive()
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


def test_straight():
    """Drive 30cm forward, verify encoder distance."""
    drive.reset_encoder_position()
    result = drive.straight(30, max_effort=0.5, timeout=5)
    left_dist = drive.get_left_encoder_position()
    right_dist = drive.get_right_encoder_position()
    avg_dist = (left_dist + right_dist) / 2
    check(f"Straight 30cm: traveled {avg_dist:.1f}cm", 25 < avg_dist < 35)
    check("Straight returned True (completed)", result is True)
    time.sleep(0.5)


def test_straight_reverse():
    """Drive 30cm backward."""
    drive.reset_encoder_position()
    result = drive.straight(-30, max_effort=0.5, timeout=5)
    avg_dist = (drive.get_left_encoder_position() + drive.get_right_encoder_position()) / 2
    check(f"Reverse 30cm: traveled {avg_dist:.1f}cm", -35 < avg_dist < -25)
    time.sleep(0.5)


def test_turn_cw():
    """Turn 90 degrees clockwise."""
    imu.reset_yaw()
    time.sleep(0.1)
    result = drive.turn(90, max_effort=0.5, timeout=5)
    yaw = imu.get_yaw()
    check(f"Turn 90 CW: yaw={yaw:.1f} degrees", 80 < yaw < 100)
    check("Turn returned True (completed)", result is True)
    time.sleep(0.5)


def test_turn_ccw():
    """Turn 90 degrees counter-clockwise."""
    imu.reset_yaw()
    time.sleep(0.1)
    drive.turn(-90, max_effort=0.5, timeout=5)
    yaw = imu.get_yaw()
    check(f"Turn 90 CCW: yaw={yaw:.1f} degrees", -100 < yaw < -80)
    time.sleep(0.5)


def test_timeout():
    """Very long distance should timeout."""
    start = time.ticks_ms()
    result = drive.straight(10000, max_effort=0.3, timeout=2)
    elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
    check(f"Timeout triggered in {elapsed:.1f}s", elapsed < 3)
    check("Timeout returned False", result is False)


def test_square():
    """Drive a square and return near starting position."""
    drive.reset_encoder_position()
    imu.reset_yaw()
    side = 20
    for i in range(4):
        drive.straight(side, max_effort=0.4, timeout=5)
        drive.turn(90, max_effort=0.4, timeout=5)
        time.sleep(0.2)
    yaw = imu.get_yaw()
    check(f"Square: final heading {yaw:.1f} degrees (expect ~360)", 340 < yaw < 380)


print("=" * 40)
print("DRIVETRAIN HARDWARE TESTS")
print("Place robot on flat surface.")
print("Press button to start.")
print("=" * 40)
board.wait_for_button()

test_straight()
test_straight_reverse()
test_turn_cw()
test_turn_ccw()
test_timeout()
test_square()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
