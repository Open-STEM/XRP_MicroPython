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

# Set to true to log the IMU heading forever
while False:
    print(imu.get_yaw())
    time.sleep(0.1)

# Turns 360 slow and fast, then turns 180 slow and fast
# IMU has accuracy issues at fast speeds.
drivetrain.turn(360, 0.5)
time.sleep(1)
drivetrain.turn(360, 0.75)
time.sleep(1)
drivetrain.turn(360, 1)