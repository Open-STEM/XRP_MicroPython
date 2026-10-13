"""
Hardware integration test for IMU.
Setup: Board on flat, stable surface. Do not move during tests.
"""
from XRPLib.imu import IMU
from XRPLib.board import Board
from teststand import is_teststand, wait_if_manual
import time

imu = IMU.get_default_imu()
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


def test_connected():
    check("IMU is connected", imu.is_connected())


def test_gravity_z():
    """Z-axis should read ~1000mg (gravity) when flat."""
    z = imu.get_acc_z()
    check(f"Gravity Z: {z:.0f}mg (expect ~1000)", 800 < z < 1200)


def test_gravity_xy():
    """X and Y should read near 0 when flat."""
    x = imu.get_acc_x()
    y = imu.get_acc_y()
    check(f"Gravity X: {x:.0f}mg (expect ~0)", abs(x) < 200)
    check(f"Gravity Y: {y:.0f}mg (expect ~0)", abs(y) < 200)


def test_gyro_at_rest():
    """Gyroscope should read near 0 when stationary (after calibration)."""
    rates = imu.get_gyro_rates()
    check(f"Gyro X: {rates[0]:.0f}mdps (expect ~0)", abs(rates[0]) < 100)
    check(f"Gyro Y: {rates[1]:.0f}mdps (expect ~0)", abs(rates[1]) < 100)
    check(f"Gyro Z: {rates[2]:.0f}mdps (expect ~0)", abs(rates[2]) < 100)


def test_yaw_stable():
    """Yaw should not drift significantly over 5 seconds at rest."""
    imu.reset_yaw()
    time.sleep(5)
    yaw = imu.get_yaw()
    check(f"Yaw drift over 5s: {yaw:.2f} degrees (expect < 3)", abs(yaw) < 3)


def test_temperature():
    """Temperature should be a reasonable room temperature."""
    temp = imu.temperature()
    check(f"Temperature: {temp:.1f}C (expect 15-45)", 15 < temp < 45)


def test_acc_gyro_batch():
    """Batch read should return 2x3 array."""
    data = imu.get_acc_gyro_rates()
    check("Batch read returns 2 rows", len(data) == 2)
    check("Batch read returns 3 cols each", len(data[0]) == 3 and len(data[1]) == 3)


print("=" * 40)
print("IMU HARDWARE TESTS")
if not is_teststand():
    print("Keep board flat and still.")
    print("Press button to start.")
print("=" * 40)
wait_if_manual(board)

test_connected()
test_gravity_z()
test_gravity_xy()
test_gyro_at_rest()
test_yaw_stable()
test_temperature()
test_acc_gyro_batch()

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
