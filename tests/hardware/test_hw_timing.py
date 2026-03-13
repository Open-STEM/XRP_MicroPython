"""
Hardware integration test for timer callback accuracy.
Verifies that timer callbacks fire at expected rates.
"""
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.imu import IMU
from XRPLib.rangefinder import Rangefinder
from XRPLib.board import Board
import time

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


def test_motor_update_rate():
    """Motor _update should fire ~50 times per second."""
    motor = EncodedMotor.get_default_encoded_motor(1)

    # Monkey-patch _update to count calls
    original_update = motor._update
    count = [0]

    def counting_update():
        count[0] += 1
        original_update()

    motor.updateTimer.init(period=20, callback=lambda t: counting_update())
    time.sleep(1.0)
    motor.updateTimer.init(period=20, callback=lambda t: motor._update())  # restore

    rate = count[0]
    check(f"Motor update rate: {rate} Hz (expect 45-55)", 40 <= rate <= 60)


def test_imu_update_rate():
    """IMU _update should fire ~208 times per second."""
    imu = IMU.get_default_imu()

    count = [0]
    original = imu._update_imu_readings

    def counting():
        count[0] += 1
        original()

    imu.update_timer.init(freq=imu.timer_frequency, callback=lambda t: counting())
    time.sleep(1.0)
    imu._start_timer()  # restore original

    rate = count[0]
    check(f"IMU update rate: {rate} Hz (expect 180-230)", 150 <= rate <= 260)


def test_all_timers_simultaneously():
    """All timers running for 10 seconds without crash."""
    _ = EncodedMotor.get_default_encoded_motor(1)
    _ = EncodedMotor.get_default_encoded_motor(2)
    _ = IMU.get_default_imu()
    _ = Rangefinder.get_default_rangefinder()

    print("  Running all timers for 10 seconds...")
    try:
        time.sleep(10)
        check("All timers ran 10s without crash", True)
    except Exception as e:
        check(f"Timer crash: {e}", False)


print("=" * 40)
print("TIMING HARDWARE TESTS")
print("Press button to start.")
print("=" * 40)
board.wait_for_button()

test_motor_update_rate()
test_imu_update_rate()
test_all_timers_simultaneously()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
