from XRPLib.drivetrain import Drivetrain
from XRPLib.encoded_motor import EncodedMotor
from XRPLib.hcsr04 import HCSR04
from XRPLib.imu import IMU
from XRPLib.led import LED
from XRPLib.reflectance import Reflectance
from XRPLib.servo import Servo
import math
import time

drivetrain = Drivetrain.get_default_drivetrain()
left_motor = EncodedMotor.get_default_left_motor()
right_motor = EncodedMotor.get_default_right_motor()
imu = IMU.get_default_imu()

imu.calibrate(5)

print("start")

imu.reset_pitch()
imu.reset_yaw()
imu.reset_roll()

def log_imu_heading():
    # Set to true to log the IMU heading forever
    while True:
        print(imu.get_yaw())
        time.sleep(0.1)

def log_encoder_position():
    while True:
        print(drivetrain.left_motor.get_position(), drivetrain.right_motor.get_position())
        time.sleep(0.1)

def benchmark_encoder_isr():
    print("start benchmark")
    N = 100000
    a = time.time()
    for i in range(N):
        drivetrain.left_motor._encoder.isr()
    b = time.time()
    
    # Print benchmark
    print("Time for {} calls: {}s".format(N, b-a))
    print("Time per call: {}s".format((b-a)/N)) # ~0.06 ms per call

def test_turns():
    # Turns 360 slow and fast, then turns 180 slow and fast
    drivetrain.turn(360, 0.5)
    time.sleep(1)
    drivetrain.turn(-360, 0.75)
    time.sleep(1)


def test_straight():
    drivetrain.straight(30, 0.2)

def test_set_effort():
    drivetrain.set_effort(0.3, 0.3)
    time.sleep(2)
    drivetrain.stop()

test_turns()